# naver-commerce-api

이 폴더의 Lambda 이름은 `naver-commerce-api`입니다. n8n에서 네이버 커머스 API를 안전하게 호출하기 위한 커머스 API Lambda입니다.

이 문서는 n8n에서 네이버 커머스 API를 반복해서 사용할 수 있도록 만드는 Lambda의 사용 방법과 운영 규칙을 설명합니다.

이 Lambda는 네이버 API를 그대로 외부에 열어주는 프록시가 아닙니다. n8n은 `operation`과 `payload`만 보내고, Lambda가 기존 인증 Lambda를 통해 토큰을 받은 뒤 허용된 네이버 API만 호출합니다.

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 런타임 | Python |
| 진입점 | `lambda_function.lambda_handler` |
| 주요 호출자 | n8n HTTP Request 노드 |
| 인증 방식 | `GenerateClientSecretSign` Lambda를 통해 네이버 `access_token` 발급 |
| 배포 산출물 | `dist/naver-commerce-api.zip` |

## 문서 구성

| 문서 | 읽는 사람 | 용도 |
| --- | --- | --- |
| `README.md` | n8n 사용자, 운영 담당자 | Lambda가 무엇인지 이해하고, n8n에서 호출하고, 실패 알림을 구성합니다. |
| `OPERATIONS.md` | n8n 사용자, 개발자 | 어떤 operation을 써야 하는지 고르고, operation별 payload와 endpoint를 확인합니다. |

처음 사용하는 사람은 이 문서를 먼저 읽고, 실제 요청 payload를 만들 때 [OPERATIONS.md](./OPERATIONS.md)를 확인합니다.

## 목적

- n8n에서 하나의 HTTP Request 노드를 네이버 커머스 작업 노드처럼 재사용합니다.
- 네이버 API 인증, endpoint, 요청 형식, 에러 형식을 Lambda 안에서 표준화합니다.
- 주문 조회, 발주 확인, 발송 처리, 교환, 반품, 취소 처리에 필요한 1차 API만 구현합니다.
- 상품, 문의, 판매자 정보 등 2차 후보는 문서에만 남기고 필요해질 때 추가합니다.

## 빠른 시작

1. n8n에서 HTTP Request 노드를 추가합니다.
2. Method를 `POST`로 설정합니다.
3. URL에 `naver-commerce-api` API Gateway URL을 입력합니다.
4. Header에 `Content-Type: application/json`을 설정합니다.
5. Body에 `operation`, `requestId`, `payload`를 넣습니다.
6. 응답의 `ok` 값으로 성공/실패를 분기합니다.
7. 실패하면 `message`, `actionHint`, `errors`, `meta.naverTraceId`를 담당자 알림에 포함합니다.

최소 요청 예시:

```json
{
  "operation": "order.getDetails",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderIds": ["1234567890"],
    "quantityClaimCompatibility": true
  }
}
```

## operation 빠른 선택

| 상황 | 사용할 operation |
| --- | --- |
| 주문번호를 상품주문번호로 바꿔야 함 | `order.getProductOrderIds` |
| 최근 변경된 주문을 주기적으로 가져와야 함 | `order.getChangedOrders` |
| 특정 상태/기간의 주문 목록을 조회해야 함 | `order.searchByCondition` |
| 상품주문 상세, 수취인, 배송지, 클레임 정보를 봐야 함 | `order.getDetails` |
| 결제완료 주문을 발주 확인 처리해야 함 | `order.confirm` |
| 상품에 설정한 품번/판매자 관리 코드를 확인해야 함 | `product.getOriginProduct` |
| 채널 상품 정보를 확인해야 함 | `product.getChannelProduct` |
| 송장번호로 발송 처리해야 함 | `delivery.dispatch` |
| 직접 전달로 발송 처리해야 함 | `delivery.dispatch` |
| 발송 기한을 늦춰야 함 | `delivery.delayDispatch` |
| 희망배송일을 변경해야 함 | `delivery.changeHopeDelivery` |
| 교환 수거를 승인해야 함 | `exchange.collectApprove` |
| 교환 상품을 새 송장으로 다시 보내야 함 | `exchange.redispatch` |
| 교환 보류/보류 해제/거부가 필요함 | `exchange.hold`, `exchange.releaseHold`, `exchange.reject` |
| 반품을 요청해야 함 | `return.request` |
| 반품을 승인해야 함 | `return.approve` |
| 반품 보류/보류 해제/거부가 필요함 | `return.hold`, `return.releaseHold`, `return.reject` |
| 취소를 요청해야 함 | `cancel.request` |
| 취소 요청을 승인해야 함 | `cancel.approve` |

전체 operation 선택 기준과 상세 payload는 [OPERATIONS.md](./OPERATIONS.md)의 "어떤 operation을 써야 하나요?" 섹션을 참고합니다.

## 전체 흐름

```text
n8n
  -> naver-commerce-api
  -> 기존 GenerateClientSecretSign Lambda
  -> Naver Commerce API
  -> naver-commerce-api
  -> n8n
```

1. n8n이 `naver-commerce-api`로 `operation`과 `payload`를 보냅니다.
2. `naver-commerce-api`가 요청 형식을 검증합니다.
3. `naver-commerce-api`가 기존 `GenerateClientSecretSign` Lambda를 호출해 `access_token`을 받습니다.
4. `naver-commerce-api`가 `operation`에 맞는 네이버 커머스 API를 호출합니다.
5. `naver-commerce-api`가 성공/실패 결과를 공통 응답 형식으로 감싸 n8n에 반환합니다.
6. n8n은 `ok` 값으로 성공/실패를 분기하고, 실패 시 담당자에게 알림을 보냅니다.

## n8n에서 호출하는 방법

n8n에서는 HTTP Request 노드를 사용합니다.

```text
Method: POST
URL: {naver-commerce-api API Gateway URL}
Headers:
  Content-Type: application/json
Body Content Type: JSON
```

요청 body는 항상 아래 형식을 사용합니다.

```json
{
  "operation": "delivery.dispatch",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {}
}
```

### 필드 설명

| 필드 | 필수 | 설명 |
| --- | :---: | --- |
| `operation` | 필수 | 실행할 작업 이름입니다. 예: `order.getDetails`, `delivery.dispatch` |
| `requestId` | 권장 | n8n 실행, Lambda 로그, 네이버 응답을 연결하기 위한 추적 ID입니다. |
| `payload` | 필수 | operation별 요청값입니다. |

`requestId`는 n8n 실행 ID를 넣는 것을 권장합니다.

```text
n8n-{{$execution.id}}
```

## 기본 응답 형식

아래 예시는 n8n에서 읽는 HTTP 응답 body 내부 JSON입니다. 실제 API Gateway Lambda 응답은 `statusCode`, `headers`, `body`로 감싼 형태입니다.

Lambda 응답 body는 성공과 실패 모두 같은 구조를 사용합니다.

### 성공 응답

```json
{
  "ok": true,
  "operation": "order.getDetails",
  "requestId": "n8n-12345",
  "message": "요청이 성공했습니다.",
  "data": {
    "timestamp": "2026-05-19T10:30:00.000+09:00",
    "traceId": "naver-trace-id",
    "data": []
  },
  "errors": [],
  "meta": {
    "naverStatusCode": 200,
    "naverTraceId": "naver-trace-id",
    "retryable": false
  }
}
```

### 실패 응답

```json
{
  "ok": false,
  "operation": "delivery.dispatch",
  "requestId": "n8n-12345",
  "errorCode": "VALIDATION_ERROR",
  "message": "필수 요청값이 누락되었습니다.",
  "actionHint": "n8n HTTP Request 노드의 payload 값을 확인하세요.",
  "data": null,
  "errors": [
    {
      "source": "adapter",
      "field": "dispatchProductOrders[0].trackingNumber",
      "message": "trackingNumber is required."
    }
  ],
  "meta": {
    "naverStatusCode": null,
    "naverTraceId": null,
    "retryable": false
  }
}
```

## 에러 처리 원칙

이 Lambda는 단순하고 유지보수 가능한 API 어댑터로 유지합니다.

Lambda가 처리하는 것:

- 지원하지 않는 `operation` 차단
- 필수 `payload` 누락 검증
- 기존 인증 Lambda 호출 실패 감지
- 네이버 API 실패를 공통 형식으로 변환
- 네이버 원본 오류 메시지와 `traceId` 전달
- 민감정보 마스킹 후 로그 기록

Lambda가 처리하지 않는 것:

- 주문 상태별 복잡한 사전 판단
- AS, 교환, 재배송 같은 업무 플로우 조건 판단
- 네이버 API를 호출하기 전 모든 경우의 수를 검사하는 precheck
- n8n의 시트/DB 행 생성 또는 업무 데이터 수정

즉, Lambda는 "네이버 API를 안전하고 일관되게 호출하는 어댑터"이고, 업무 흐름은 n8n이 담당합니다.

## 에러 코드

| errorCode | 의미 | 담당자가 확인할 것 | retryable |
| --- | --- | --- | :---: |
| `INVALID_REQUEST` | body가 JSON이 아니거나 기본 형식이 잘못됨 | n8n HTTP Request 노드 body 형식 | No |
| `UNSUPPORTED_OPERATION` | 등록되지 않은 operation 요청 | operation 이름 오타 또는 미구현 operation 여부 | No |
| `VALIDATION_ERROR` | 필수 payload 누락 | 응답의 `errors[].field` 값 | No |
| `AUTH_ERROR` | 기존 인증 Lambda 호출 실패 또는 토큰 없음 | 인증 Lambda URL, client ID/secret 환경변수, 인증 Lambda 로그 | 상황별 |
| `NAVER_API_ERROR` | 네이버 API가 4xx/5xx 응답 반환 | `errors[].message`, `meta.naverStatusCode`, `meta.naverTraceId` | 상황별 |
| `NAVER_TIMEOUT` | 네이버 API 응답 시간 초과 | 잠시 후 재시도, 네이버 장애 여부 | Yes |
| `LAMBDA_INTERNAL_ERROR` | `naver-commerce-api` 내부 오류 | Lambda 로그의 `requestId` 검색 | 상황별 |

## 실패 알림 예시

n8n에서는 `ok = false`일 때 아래처럼 담당자 알림을 만들 수 있습니다.

```text
[네이버 커머스 API 실패]

작업: {{$json.operation}}
요청 ID: {{$json.requestId}}
오류 코드: {{$json.errorCode}}
원인: {{$json.message}}
조치: {{$json.actionHint}}
재시도 가능: {{$json.meta.retryable}}
네이버 상태 코드: {{$json.meta.naverStatusCode}}
네이버 Trace ID: {{$json.meta.naverTraceId}}
상세 오류: {{$json.errors}}
```

## 자주 쓰는 n8n 요청 예시

### 상품 주문 상세 조회

```json
{
  "operation": "order.getDetails",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderIds": ["1234567890", "1234567891"],
    "quantityClaimCompatibility": true
  }
}
```

### 변경 주문 조회

```json
{
  "operation": "order.getChangedOrders",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "lastChangedFrom": "2026-05-19T00:00:00.000+09:00",
    "lastChangedTo": "2026-05-19T23:59:59.999+09:00",
    "lastChangedType": "PAYED",
    "limitCount": 300
  }
}
```

### 발주 확인

```json
{
  "operation": "order.confirm",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderIds": ["1234567890", "1234567891"]
  }
}
```

### 발송 처리

일반 택배는 택배사 코드와 송장번호를 함께 보냅니다.

```json
{
  "operation": "delivery.dispatch",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "dispatchProductOrders": [
      {
        "productOrderId": "1234567890",
        "deliveryMethod": "DELIVERY",
        "deliveryCompanyCode": "HANJIN",
        "trackingNumber": "111122223333",
        "dispatchDate": "2026-05-19T10:30:00.000+09:00"
      }
    ]
  }
}
```

직접 전달은 택배사 코드와 송장번호를 생략합니다.

```json
{
  "operation": "delivery.dispatch",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "dispatchProductOrders": [
      {
        "productOrderId": "1234567890",
        "deliveryMethod": "DIRECT_DELIVERY",
        "dispatchDate": "2026-05-19T10:30:00.000+09:00"
      }
    ]
  }
}
```

### 교환 재배송 처리

일반 택배 재배송은 택배사 코드와 송장번호를 함께 보냅니다.

```json
{
  "operation": "exchange.redispatch",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderId": "1234567890",
    "reDeliveryMethod": "DELIVERY",
    "reDeliveryCompany": "HANJIN",
    "reDeliveryTrackingNumber": "111122223333"
  }
}
```

직접 전달 재배송은 택배사 코드와 송장번호를 생략합니다.

```json
{
  "operation": "exchange.redispatch",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderId": "1234567890",
    "reDeliveryMethod": "DIRECT_DELIVERY"
  }
}
```

### 반품 승인

```json
{
  "operation": "return.approve",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

### 취소 승인

```json
{
  "operation": "cancel.approve",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

## 구현 대상 operation

1차 구현 대상은 주문 처리에 직접 필요한 operation입니다.

| 영역 | operation |
| --- | --- |
| 주문 조회 | `order.getProductOrderIds`, `order.getChangedOrders`, `order.searchByCondition`, `order.getDetails` |
| 상품 조회 | `product.getOriginProduct`, `product.getChannelProduct` |
| 발주/배송 | `order.confirm`, `delivery.dispatch`, `delivery.delayDispatch`, `delivery.changeHopeDelivery` |
| 교환 | `exchange.collectApprove`, `exchange.redispatch`, `exchange.hold`, `exchange.releaseHold`, `exchange.reject` |
| 반품 | `return.request`, `return.approve`, `return.hold`, `return.releaseHold`, `return.reject` |
| 취소 | `cancel.request`, `cancel.approve` |

각 operation의 endpoint와 payload는 [OPERATIONS.md](./OPERATIONS.md)를 참고합니다.

operation 선택이 헷갈리면 [OPERATIONS.md](./OPERATIONS.md)의 "어떤 operation을 써야 하나요?"와 "대표 n8n 흐름" 섹션을 먼저 확인합니다. 그 섹션은 n8n 사용자가 상황별로 어떤 작업을 호출해야 하는지 판단하기 위한 안내입니다.

## 추후 확장 후보

아래 operation은 당장 구현하지 않고, 필요해질 때 추가합니다.

| 영역 | 후보 operation | 용도 |
| --- | --- | --- |
| 상품 | `product.search` | 상품 목록 조회 |
| 상품 | `product.changeStatus` | 판매 중, 품절, 판매 중지 변경 |
| 상품 | `product.updateOptionStock` | 옵션 재고 변경 |
| 문의 | `qna.listCustomerInquiries` | 고객 문의 조회 |
| 문의 | `qna.listProductQnas` | 상품 문의 조회 |
| 문의 | `qna.answerProductQna` | 상품 문의 답변 등록/수정 |
| 판매자 | `seller.getAccount` | 연결된 판매자 계정 확인 |
| 판매자 | `seller.getChannels` | 연결된 채널 정보 확인 |
| 운영 보조 | `seller.getLogisticsCompanies` | 연동 물류사 확인. 택배사가 고정이면 우선순위 낮음 |
| 운영 보조 | `seller.getWarehouses` | 출고 창고/물류사 매핑 확인. 출고지 자동 분기 필요 시 추가 |
| 운영 보조 | `delivery.getReturnDeliveryCompanies` | 반품/교환 택배사 코드 목록 확인. 수거 송장번호 조회용은 아님 |

## Lambda 환경변수

| 이름 | 필수 | 설명 |
| --- | :---: | --- |
| `NAVER_AUTH_API_URL` | 필수 | 기존 `GenerateClientSecretSign` Lambda의 API Gateway URL |
| `NAVER_CLIENT_ID` | 필수 | 네이버 커머스 API client ID |
| `NAVER_CLIENT_SECRET` | 필수 | 네이버 커머스 API client secret |
| `NAVER_ACCOUNT_TYPE` | 선택 | 기본값: `SELF`. `SELLER` 계정이면 명시 |
| `NAVER_ACCOUNT_ID` | 조건부 | `NAVER_ACCOUNT_TYPE=SELLER`일 때 필수 |
| `NAVER_API_BASE_URL` | 선택 | 기본값: `https://api.commerce.naver.com/external` |
| `REQUEST_TIMEOUT_SECONDS` | 선택 | 기본값: `20`. 정수만 허용 |
| `LOG_LEVEL` | 선택 | 기본값: `INFO` |

`REQUEST_TIMEOUT_SECONDS`에 숫자가 아닌 값을 넣으면 Lambda 초기 설정 단계에서 오류가 발생합니다.

## 배포 패키지

배포 zip은 제공된 스크립트로 생성합니다.

```bash
./scripts/build_package.sh
```

성공하면 아래 파일이 생성됩니다.

```text
dist/naver-commerce-api.zip
```

현재 스크립트는 `requirements.txt` 설치를 수행하지 않고 소스 폴더를 그대로 zip으로 묶습니다. 현재 구현은 외부 Python 패키지 의존성이 없어 이 방식으로 동작합니다. 외부 의존성이 추가되면 스크립트에 의존성 설치 단계를 추가해야 합니다.

## 로그 규칙

Lambda는 JSON 형태의 구조화 로그를 남깁니다.

남겨야 하는 값:

- `requestId`
- `operation`
- `step`
- `errorCode`
- `naverStatusCode`
- `naverTraceId`
- 요청 건수 같은 요약 정보

남기면 안 되는 값:

- `access_token`
- `client_secret`
- `client_secret_sign`
- 구매자 전화번호 전체
- 배송지 상세주소 전체
- 주민번호, 개인통관고유부호 등 민감정보

예시:

```json
{
  "level": "ERROR",
  "requestId": "n8n-12345",
  "operation": "delivery.dispatch",
  "step": "call_naver_api",
  "errorCode": "NAVER_API_ERROR",
  "message": "Naver API returned error.",
  "naverStatusCode": 400,
  "naverTraceId": "abc-def",
  "payloadSummary": {
    "productOrderIdCount": 1,
    "deliveryCompanyCode": "HANJIN"
  }
}
```

## 구현 원칙

- n8n이 네이버 endpoint를 직접 보내는 방식은 허용하지 않습니다.
- Lambda는 등록된 `operation`만 실행합니다.
- Lambda는 필수 payload만 검증합니다.
- 주문 상태별 복잡한 업무 판단은 n8n 또는 담당자가 처리합니다.
- 네이버 원본 응답은 `data` 또는 `errors[].detail` 안에 보존합니다.
- 네이버 `traceId`가 있으면 반드시 응답과 로그에 포함합니다.
- 상태 변경 operation은 네이버 API가 부분 성공/부분 실패를 반환할 수 있으므로, n8n은 응답의 성공/실패 목록을 확인해야 합니다.

## 참고 문서

- [네이버 커머스 API RESTful API 공통 규칙](https://apicenter.commerce.naver.com/docs/restful-api)
- [네이버 커머스 API LLM 문서 인덱스](https://apicenter.commerce.naver.com/llms/llms.txt)

## 변경 이력

| 날짜 | 변경 내용 |
| --- | --- |
| 2026-05-20 | README.md 형식 보완, operation 빠른 선택/응답 예시/배포 섹션 정리 |
| 2026-05-20 | Lambda 명칭을 폴더명 기준 `naver-commerce-api`로 통일 |
| 2026-05-20 | 개발 계획 문서 제거에 맞춰 문서 구성 정리 |
