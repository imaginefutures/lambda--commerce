# motitorContetntBuyer

아임웹 다운로드 상품 주문 중 구매확정 상태의 주문을 확인하고, 처리 대상 주문을 Zapier Webhook으로 전달하는 운영 자동화 Lambda입니다.

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 런타임 | Python |
| 진입점 | `lambda_function.lambda_handler` |
| 트리거 | EventBridge 스케줄 또는 Zapier 호출 |
| 요청 body | 사용하지 않음 |
| 외부 서비스 | IMWEB API, Zapier Webhook, DynamoDB |

## 역할

이 Lambda는 주기적으로 IMWEB 주문을 조회해 아래 조건을 만족하는 주문을 처리합니다.

- 주문 상태: `PURCHASE_CONFIRMATION`
- 주문 범위: 실행 시점 기준 최근 2일
- 배송 방식: `payment.deliv_type == "download"`
- 중복 여부: `PROWOrderContentHistory`에 같은 `order_no`가 없어야 함

처리 대상 주문은 상품별로 Zapier Webhook에 전달하고, 주문 단위로 DynamoDB에 처리 기록을 남깁니다.

## 처리 흐름

1. 환경변수의 IMWEB API key/secret으로 IMWEB `access_token`을 발급합니다.
2. 최근 2일간의 `PURCHASE_CONFIRMATION` 주문을 조회합니다.
3. 다운로드 배송 주문만 필터링합니다.
4. `PROWOrderContentHistory`에서 `order_no` 기준으로 중복 처리 여부를 확인합니다.
5. 주문 상세 API를 호출해 상품명, 옵션, 커스텀코드, 주문자 전화번호를 읽습니다.
6. 전화번호로 `PROWDiscordUser`의 `phone-index`를 조회해 Discord 가입 여부와 `userID`를 확인합니다.
7. 상품별 payload를 Zapier Webhook으로 전송합니다.
8. 주문 처리 기록을 `PROWOrderContentHistory`에 저장합니다.

현재 구현은 Webhook 전송 실패 여부와 관계없이 주문 단위 처리 완료 기록을 진행합니다. 이 동작을 바꾸려면 `send_webhook()` 반환값을 확인해 모든 상품 전송 성공 시에만 기록하도록 코드 수정이 필요합니다.

## 환경변수

| 이름 | 필수 | 설명 |
| --- | :---: | --- |
| `IMWEB_API_KEY` | 필수 | IMWEB 인증 key |
| `IMWEB_API_SECRET` | 필수 | IMWEB 인증 secret |
| `ZAPIER_WEBHOOK_URL` | 필수 | 주문 정보를 전달할 Zapier Webhook URL |

## DynamoDB

| 테이블 | 사용 방식 | 필요한 키/인덱스 |
| --- | --- | --- |
| `PROWOrderContentHistory` | 주문 중복 확인 및 처리 완료 기록 | `order_no` 파티션 키 |
| `PROWDiscordUser` | 전화번호로 Discord 가입 여부 조회 | `phone-index` GSI, `phone` 키 |

`PROWOrderContentHistory`에는 아래 값이 저장됩니다.

```json
{
  "order_no": "주문번호",
  "phone": "주문자 전화번호",
  "program": "첫 번째 상품명",
  "period": "계산된 이용 기간"
}
```

## Zapier Payload

상품별로 아래 형식의 JSON을 전송합니다.

```json
{
  "order_no": ["주문번호"],
  "prod_name": ["상품명"],
  "call": ["주문자 전화번호"],
  "value_name_list": ["기간"],
  "userID": ["Discord userID"],
  "디스코드 가입 여부": ["가입"],
  "is_subscription": ["구독"]
}
```

`send_webhook()`은 최대 3회 재시도하고, 재시도 간격은 2초입니다.

## 기간 계산 규칙

1. 상품 옵션의 `value_name_list`가 있으면 첫 번째 값을 사용합니다.
2. `prod_custom_code == "BEPL-MEMBERSHIP-365"`이면 기간은 항상 `1개월`입니다.
3. 옵션값이 없고 상품명에 `우아한 영어`가 포함되면 `36개월`입니다.
4. 그 외 옵션값이 없는 일반 콘텐츠는 `12개월`입니다.

`prod_custom_code == "BEPL-MEMBERSHIP-365"`이면 Zapier payload의 `is_subscription` 값은 `구독`입니다. 그 외 상품은 현재 코드상 `'` 값이 들어갑니다.

## 성공 응답

```json
{
  "statusCode": 200,
  "body": "3건 처리 완료"
}
```

`body`의 숫자는 조회된 다운로드 주문 수입니다. 실제 신규 처리 성공 건수나 Webhook 성공 건수와 다를 수 있습니다.

## 실패 응답

전체 처리 중 예외가 발생하면 아래 응답을 반환합니다.

```json
{
  "statusCode": 500,
  "body": "에러 발생"
}
```

## 배포 패키지

GitHub에는 설치된 Python 패키지 폴더를 커밋하지 않습니다. 배포 전 패키지를 새로 생성합니다.

```bash
rm -rf .build motitorContetntBuyer.zip
mkdir -p .build
python -m pip install -r requirements.txt -t .build
cp lambda_function.py .build/
cd .build
zip -qr ../motitorContetntBuyer.zip .
```

AWS Lambda 런타임에 포함된 `boto3`는 별도로 패키징하지 않습니다.

## 로그와 보안

- IMWEB `access_token`, API key/secret, Zapier Webhook URL은 로그에 남기지 않습니다.
- 전화번호, Discord `userID`, 주문 상세 payload 전체를 로그에 남기지 않습니다.
- 운영 로그 공유 시 주문번호와 전화번호는 마스킹합니다.
- Webhook URL은 환경변수 또는 Secrets Manager로 관리하고 GitHub에 커밋하지 않습니다.

## 변경 이력

| 날짜 | 변경 내용 |
| --- | --- |
| 2025-04-14 | 다운로드 주문 추적 및 Zapier 연동 구조 구축 |
| 2026-05-20 | README.md 형식 통일, 최근 2일 조회/DynamoDB/Discord/구독 로직 반영 |

