# naver-commerce-api Development Plan

이 문서는 `naver-commerce-api` Lambda를 개발하기 전에 구현해야 할 기능, 제외할 범위, 모듈 구조, 완료 기준을 정의합니다.

목표는 n8n에서 `operation + payload` 형식으로 네이버 커머스 API를 일관되게 호출할 수 있는 Lambda를 만드는 것입니다.

## 개발 목표

이 Lambda는 n8n과 네이버 커머스 API 사이의 어댑터입니다.

Lambda가 책임지는 것:

- n8n 요청 body 파싱
- `operation` 기반 라우팅
- operation별 필수 payload 검증
- 기존 `GenerateClientSecretSign` Lambda를 통한 access token 발급
- 네이버 커머스 API 호출
- 성공/실패 응답 표준화
- requestId 기반 구조화 로그
- 민감정보 마스킹

Lambda가 책임지지 않는 것:

- 네이버 인증 서명 직접 생성
- n8n 업무 플로우 판단
- 주문 상태별 복잡한 precheck
- 시트/DB 행 생성 또는 수정
- 담당자 알림 발송
- 2차 후보 API 구현

## 1차 구현 범위

### 주문 조회

| operation | 구현 내용 |
| --- | --- |
| `order.getProductOrderIds` | 주문번호로 상품주문번호 목록 조회 |
| `order.getChangedOrders` | 변경 상품주문 내역 조회 |
| `order.searchByCondition` | 조건형 상품주문 상세 목록 조회 |
| `order.getDetails` | 상품주문번호 배열로 상세 조회 |

### 발주/배송

| operation | 구현 내용 |
| --- | --- |
| `order.confirm` | 발주 확인 처리 |
| `delivery.dispatch` | 발송 처리 |
| `delivery.delayDispatch` | 발송 지연 처리 |
| `delivery.changeHopeDelivery` | 배송 희망일 변경 처리 |

### 교환

| operation | 구현 내용 |
| --- | --- |
| `exchange.collectApprove` | 교환 수거 완료 |
| `exchange.redispatch` | 교환 재배송 처리 |
| `exchange.hold` | 교환 보류 |
| `exchange.releaseHold` | 교환 보류 해제 |
| `exchange.reject` | 교환 거부 또는 철회 |

### 반품

| operation | 구현 내용 |
| --- | --- |
| `return.request` | 반품 요청 |
| `return.approve` | 반품 승인 |
| `return.hold` | 반품 보류 |
| `return.releaseHold` | 반품 보류 해제 |
| `return.reject` | 반품 거부 또는 철회 |

### 취소

| operation | 구현 내용 |
| --- | --- |
| `cancel.request` | 취소 요청 |
| `cancel.approve` | 취소 요청 승인 |

## 구현 제외 범위

아래 operation은 문서에만 남기고 이번 개발 범위에서는 제외합니다.

| operation | 제외 이유 |
| --- | --- |
| `product.search` | 상품 운영 자동화가 아직 확정되지 않음 |
| `product.changeStatus` | 판매 상태 변경 정책이 필요함 |
| `product.updateOptionStock` | 재고 자동화 정책이 필요함 |
| `qna.listCustomerInquiries` | 문의 처리 자동화가 아직 확정되지 않음 |
| `qna.listProductQnas` | 상품 문의 처리 방식이 아직 확정되지 않음 |
| `qna.answerProductQna` | 답변 템플릿/검수 정책이 필요함 |
| `seller.getAccount` | 초기 연결 확인용이며 상시 업무 필요성이 낮음 |
| `seller.getChannels` | 초기 연결 확인용이며 상시 업무 필요성이 낮음 |
| `seller.getLogisticsCompanies` | 택배사/물류사 설정 확인용이며, 현재 택배사가 고정이라 1차 필수 아님 |
| `seller.getWarehouses` | 출고지 자동 분기 필요 시 유용하지만 현재 1차 업무 범위 아님 |
| `delivery.getReturnDeliveryCompanies` | 반품/교환 택배사 코드 목록 조회용이며, 수거 송장번호 조회용이 아님 |

## 요청/응답 계약

### n8n 요청

```json
{
  "operation": "delivery.dispatch",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {}
}
```

필수 규칙:

- `operation`은 문자열이어야 합니다.
- `payload`는 object여야 합니다.
- `requestId`가 없으면 Lambda가 자체 request ID를 생성합니다.
- n8n이 `method`, `endpoint`, `headers`를 직접 보내 네이버 API를 호출하는 방식은 허용하지 않습니다.

### 성공 응답

```json
{
  "ok": true,
  "operation": "delivery.dispatch",
  "requestId": "n8n-12345",
  "message": "요청이 성공했습니다.",
  "data": {},
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

## 에러 처리 기능

### 구현할 에러 코드

| errorCode | 발생 조건 | HTTP statusCode | retryable |
| --- | --- | :---: | :---: |
| `INVALID_REQUEST` | JSON 파싱 실패, body 형식 오류 | 400 | false |
| `UNSUPPORTED_OPERATION` | catalog에 없는 operation | 400 | false |
| `VALIDATION_ERROR` | 필수 payload 누락 | 400 | false |
| `AUTH_ERROR` | 인증 Lambda 호출 실패 또는 access_token 없음 | 502 | 상황별 |
| `NAVER_API_ERROR` | 네이버 API가 4xx/5xx 반환 | 네이버 status 반영 | 상황별 |
| `NAVER_TIMEOUT` | 인증 또는 네이버 API timeout | 504 | true |
| `LAMBDA_INTERNAL_ERROR` | 예상하지 못한 내부 오류 | 500 | false |

### 에러 메시지 원칙

- Lambda가 확실히 아는 문제만 구체적으로 설명합니다.
- 필수값 누락은 `errors[].field`에 정확한 필드 경로를 반환합니다.
- 네이버 API 실패는 네이버 원본 메시지, status code, traceId를 보존합니다.
- 주문 상태별 실패 원인은 Lambda가 추정하지 않습니다.
- 담당자 알림에는 `message`, `actionHint`, `errorCode`, `errors`, `meta.naverTraceId`를 사용합니다.

## 로그 기능

### 로그 형식

Lambda 로그는 JSON 형태의 구조화 로그로 남깁니다.

필수 로그 필드:

| 필드 | 설명 |
| --- | --- |
| `level` | `INFO`, `WARN`, `ERROR` |
| `requestId` | n8n 요청 ID 또는 Lambda 생성 ID |
| `operation` | 실행 operation |
| `step` | 처리 단계 |
| `message` | 로그 메시지 |
| `errorCode` | 실패 시 에러 코드 |
| `naverStatusCode` | 네이버 HTTP 상태 코드 |
| `naverTraceId` | 네이버 traceId |
| `payloadSummary` | 민감정보를 제외한 요청 요약 |

### 로그 단계

| step | 시점 |
| --- | --- |
| `parse_request` | n8n 요청 파싱 |
| `validate_request` | operation과 payload 검증 |
| `get_access_token` | 기존 인증 Lambda 호출 |
| `call_naver_api` | 네이버 API 호출 |
| `build_response` | 표준 응답 생성 |

### 로그 금지 값

- `access_token`
- `client_secret`
- `client_secret_sign`
- 구매자 전화번호 전체
- 배송지 상세주소 전체
- 개인통관고유부호 등 민감정보

## 모듈 구조

구현할 파일 구조:

```text
naver-commerce-api/
  lambda_function.py
  requirements.txt
  README.md
  OPERATIONS.md
  DEVELOPMENT_PLAN.md
  scripts/
    build_package.sh
  common/
    __init__.py
    config.py
    errors.py
    http_client.py
    logging.py
    response.py
    validation.py
  clients/
    __init__.py
    naver_auth_client.py
    naver_api_client.py
  operations/
    __init__.py
    catalog.py
    router.py
    transforms.py
  tests/
    test_lambda_function.py
    test_validation.py
    test_router.py
    test_response.py
```

### `lambda_function.py`

역할:

- API Gateway event body 파싱
- `AdapterService` 또는 router 호출
- 최종 `statusCode`, `headers`, `body` 반환
- 예상하지 못한 오류를 `LAMBDA_INTERNAL_ERROR`로 변환

### `common/config.py`

역할:

- Lambda 환경변수 로딩
- 기본값 정의
- 필수 환경변수 누락 검증

필요 환경변수:

| 이름 | 필수 | 설명 |
| --- | :---: | --- |
| `NAVER_AUTH_API_URL` | Yes | 기존 인증 Lambda API Gateway URL |
| `NAVER_CLIENT_ID` | Yes | 네이버 client ID |
| `NAVER_CLIENT_SECRET` | Yes | 네이버 client secret |
| `NAVER_ACCOUNT_TYPE` | Yes | 보통 `SELF` |
| `NAVER_ACCOUNT_ID` | No | `SELLER` 타입일 때 사용 |
| `NAVER_API_BASE_URL` | No | 기본값 `https://api.commerce.naver.com/external` |
| `REQUEST_TIMEOUT_SECONDS` | No | 기본값 `20` |
| `LOG_LEVEL` | No | 기본값 `INFO` |

### `clients/naver_auth_client.py`

역할:

- 기존 `GenerateClientSecretSign` Lambda 호출
- `access_token` 추출
- 인증 실패를 `AUTH_ERROR`로 변환

요청 payload:

```json
{
  "client_id": "{NAVER_CLIENT_ID}",
  "client_secret": "{NAVER_CLIENT_SECRET}",
  "type": "{NAVER_ACCOUNT_TYPE}"
}
```

`NAVER_ACCOUNT_TYPE=SELLER`이면 `account_id`를 포함합니다.

### `clients/naver_api_client.py`

역할:

- 네이버 API 호출 공통 처리
- Authorization 헤더 추가
- query/body 전달
- 네이버 오류 응답을 표준 오류로 변환할 수 있게 원본 응답 보존

### `operations/catalog.py`

역할:

- 지원 operation 목록 정의
- method, path, required fields, query fields, body fields 정의

예:

```python
{
    "delivery.dispatch": {
        "method": "POST",
        "path": "/v1/pay-order/seller/product-orders/dispatch",
        "required": [
            "dispatchProductOrders",
            "dispatchProductOrders[].productOrderId",
            "dispatchProductOrders[].deliveryMethod",
            "dispatchProductOrders[].deliveryCompanyCode",
            "dispatchProductOrders[].trackingNumber",
            "dispatchProductOrders[].dispatchDate",
        ],
        "body": ["dispatchProductOrders"],
    }
}
```

### `operations/router.py`

역할:

- operation catalog 조회
- payload 검증 호출
- path/query/body 구성
- auth client와 naver api client를 이용해 실제 호출

### `common/validation.py`

역할:

- 필수 field 검증
- 배열 내부 필수값 검증
- 검증 실패 시 field path 목록 반환

검증 예:

```text
dispatchProductOrders[0].trackingNumber is required.
```

### `common/response.py`

역할:

- 성공 응답 생성
- 실패 응답 생성
- API Gateway 응답 생성
- 네이버 traceId 추출

### `common/logging.py`

역할:

- 구조화 로그 출력
- payload summary 생성
- 민감정보 마스킹

## 개발 순서

### 1단계: 프로젝트 기본 구조 생성

완료 기준:

- 위 모듈 구조 생성
- `lambda_function.lambda_handler` 진입점 생성
- 빈 요청, 잘못된 JSON, unsupported operation 응답 확인

### 2단계: 공통 응답/에러/검증 구현

완료 기준:

- 모든 실패가 표준 실패 응답 형식으로 반환됨
- 필수 payload 누락 시 네이버 API를 호출하지 않음
- 테스트로 `VALIDATION_ERROR`, `UNSUPPORTED_OPERATION`, `INVALID_REQUEST` 확인

### 3단계: 인증 Lambda 연동

완료 기준:

- 기존 인증 Lambda 호출
- `access_token` 추출
- 토큰 누락/인증 실패 시 `AUTH_ERROR` 반환
- 로그에 토큰과 client secret이 남지 않음

### 4단계: 네이버 API client 구현

완료 기준:

- GET/POST 공통 호출 가능
- query/body/path parameter 처리 가능
- 네이버 4xx/5xx 응답 원문 보존
- timeout 처리 가능

### 5단계: operation catalog와 router 구현

완료 기준:

- 1차 구현 범위 operation이 catalog에 모두 등록됨
- 각 operation이 올바른 method/path/query/body로 변환됨
- path parameter가 payload에서 endpoint로 삽입됨

### 6단계: operation별 테스트 작성

완료 기준:

- 각 operation의 request 변환 테스트
- 필수값 누락 테스트
- 네이버 성공 응답 표준화 테스트
- 네이버 실패 응답 표준화 테스트

### 7단계: 패키징 스크립트 작성

완료 기준:

- `scripts/build_package.sh`로 Lambda 배포 zip 생성
- 테스트 파일과 캐시 파일은 배포 zip에서 제외
- `dist/naver-commerce-api.zip` 생성

### 8단계: README/OPERATIONS 동기화

완료 기준:

- 구현된 operation과 문서의 operation 목록 일치
- 환경변수 목록 일치
- n8n 예시 payload가 실제 validation을 통과함

## 테스트 범위

필수 테스트:

| 테스트 | 목적 |
| --- | --- |
| body 파싱 테스트 | API Gateway string body와 dict body 처리 |
| unsupported operation 테스트 | 허용되지 않은 operation 차단 |
| validation 테스트 | 필수 payload 누락 검증 |
| router 테스트 | operation을 method/path/query/body로 변환 |
| auth error 테스트 | 인증 Lambda 실패 표준화 |
| naver error 테스트 | 네이버 오류 응답 표준화 |
| response 테스트 | 성공/실패 응답 형식 유지 |
| masking 테스트 | 민감정보 로그 제외 |

## 완료 기준

개발 완료로 보는 기준:

- 1차 구현 범위 operation이 모두 catalog에 등록되어 있음
- 각 operation의 필수 payload 검증이 동작함
- 기존 인증 Lambda를 통해 access token을 가져옴
- 네이버 API 호출 성공/실패가 표준 응답으로 반환됨
- n8n이 `ok` 값으로 성공/실패를 분기할 수 있음
- 실패 응답만 보고 담당자가 확인할 값과 조치 방향을 알 수 있음
- 로그에 `requestId`, `operation`, `step`, `errorCode`가 남음
- 로그에 토큰, client secret, 상세 개인정보가 남지 않음
- 테스트가 통과함
- 배포 zip 생성 스크립트가 동작함

## 구현 리스크

| 리스크 | 대응 |
| --- | --- |
| 네이버 API 응답 구조가 operation마다 다름 | Lambda는 원본 응답을 최대한 보존하고, 공통 wrapper만 씌움 |
| 네이버 상태 변경 API가 부분 성공을 반환함 | n8n이 `successProductOrderIds`, `failProductOrderInfos`를 확인하도록 문서화 |
| 인증 Lambda가 민감값을 로그로 남길 수 있음 | 기존 인증 Lambda도 추후 로그 정리 필요 |
| operation이 계속 늘어나 router가 커짐 | catalog 기반으로 추가하고, 업무 로직은 n8n에 둠 |
| 친절한 에러 구현이 과해짐 | 필수값 검증과 네이버 원본 오류 전달까지만 담당 |
