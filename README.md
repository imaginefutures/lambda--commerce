# lambda--commerce

이 저장소는 커머스 운영에 사용하는 AWS Lambda 함수 3개를 관리합니다.

## Lambda 목록

| 폴더 | 역할 | 런타임 | 진입점 | 주요 호출자 |
| --- | --- | --- | --- | --- |
| `GenerateClientSecretSign` | 네이버 커머스 API `access_token` 발급 | Node.js | `index.handler` | `naver-commerce-api` |
| `naver-commerce-api` | n8n에서 네이버 커머스 API를 안전하게 호출하는 어댑터 | Python | `lambda_function.lambda_handler` | n8n |
| `motitorContetntBuyer` | 아임웹 다운로드 상품 구매확정 주문을 Zapier로 전달 | Python | `lambda_function.lambda_handler` | EventBridge 정기 스케줄 |

`motitorContetntBuyer` 폴더명은 기존 배포명과의 호환을 위해 그대로 둡니다.

## 전체 흐름

```text
n8n
  -> naver-commerce-api
  -> GenerateClientSecretSign
  -> Naver Commerce API
  -> naver-commerce-api
  -> n8n

EventBridge 정기 스케줄
  -> motitorContetntBuyer
  -> IMWEB API
  -> DynamoDB
  -> Zapier Webhook
```

## 문서 구조

각 Lambda의 상세 동작, 입력값, 환경변수, 배포 방법은 폴더별 README를 기준으로 확인합니다.

- [GenerateClientSecretSign](./GenerateClientSecretSign/README.md)
- [naver-commerce-api](./naver-commerce-api/README.md)
- [motitorContetntBuyer](./motitorContetntBuyer/README.md)

## GitHub 업로드 기준

저장소에는 소스 코드, 의존성 명세, 문서만 올립니다.

커밋하지 않는 항목:

- `node_modules/`
- Python 패키지 설치 폴더(`requests/`, `urllib3/`, `certifi/` 등)
- `.env`, `.env.*`
- `.DS_Store`
- `.build/`, `dist/`, `*.zip`

배포 패키지는 각 Lambda 폴더의 README에 있는 방식으로 로컬 또는 CI에서 다시 생성합니다.

## 공통 보안 규칙

- `access_token`, `client_secret`, `client_secret_sign`, 웹훅 URL, 전화번호 전체값은 로그에 남기지 않습니다.
- API Gateway와 Lambda 호출 권한은 필요한 내부 서비스에만 허용합니다.
- 환경변수 값은 GitHub에 커밋하지 않고 AWS Lambda 환경변수 또는 Secrets Manager에서 관리합니다.
- 운영 로그를 공유할 때는 주문번호, 전화번호, 토큰, 주소 등 식별 가능한 값을 마스킹합니다.

## 공통 배포 전 점검

1. 각 Lambda 폴더의 README와 실제 코드가 맞는지 확인합니다.
2. 필요한 환경변수가 AWS Lambda에 설정되어 있는지 확인합니다.
3. 배포 zip에 소스와 필요한 의존성만 포함되어 있는지 확인합니다.
4. 테스트 요청을 1회 실행해 성공 응답과 CloudWatch 로그를 확인합니다.
5. 실패 응답이 운영자가 조치할 수 있는 메시지를 포함하는지 확인합니다.

## 변경 이력

| 날짜 | 변경 내용 |
| --- | --- |
| 2026-05-20 | GitHub 업로드를 위한 루트 README 추가, Lambda별 README 형식 통일 |
| 2026-05-20 | 프로젝트명을 `lambda--commerce`로 정리 |
