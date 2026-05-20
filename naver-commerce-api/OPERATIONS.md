# naver-commerce-api Operations

이 문서는 `naver-commerce-api`가 지원하는 `operation`별 네이버 endpoint, 필수 payload, 선택 payload를 정의합니다.

n8n 사용자는 이 문서의 예시를 참고해 `operation`과 `payload`를 구성하면 됩니다. 개발자는 이 문서를 라우팅 테이블과 검증 규칙의 기준으로 사용합니다.

## 이 문서를 읽는 방법

이 문서는 처음부터 끝까지 읽는 문서가 아니라, 필요한 operation을 찾아보는 참조 문서입니다.

| 목적 | 볼 섹션 |
| --- | --- |
| 어떤 operation을 써야 할지 고르기 | "어떤 operation을 써야 하나요?" |
| n8n 전체 흐름 예시 보기 | "대표 n8n 흐름" |
| payload 필수값 확인하기 | 각 operation 상세 섹션 |
| 배송 방법, 택배사 코드, 보류 유형 확인하기 | "공통 코드값" |
| 개발자가 라우팅 구현 기준 확인하기 | "라우팅 구현 기준" |
| 지금은 구현하지 않을 API 확인하기 | "구현 보류 operation" |

## 목차

- [공통 규칙](#공통-규칙)
- [응답 확인 기준](#응답-확인-기준)
- [공통 코드값](#공통-코드값)
- [Operation 목록](#operation-목록)
- [어떤 operation을 써야 하나요?](#어떤-operation을-써야-하나요)
- [대표 n8n 흐름](#대표-n8n-흐름)
- [주문 조회](#주문-조회)
- [발주/배송](#발주배송)
- [교환](#교환)
- [반품](#반품)
- [취소](#취소)
- [구현 보류 operation](#구현-보류-operation)
- [라우팅 구현 기준](#라우팅-구현-기준)

## 공통 규칙

공통 Base URL:

```text
https://api.commerce.naver.com/external
```

n8n 요청 형식:

```json
{
  "operation": "order.getDetails",
  "requestId": "n8n-{{$execution.id}}",
  "payload": {}
}
```

네이버 API 호출 공통 헤더:

```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

날짜/시간 값은 ISO 8601 형식을 사용합니다.

```text
2026-05-19T10:30:00.000+09:00
```

날짜 값만 필요한 경우는 API 설명에 맞게 `yyyy-MM-dd` 또는 `yyyyMMdd`를 사용합니다.

## 응답 확인 기준

네이버 상태 변경 API는 HTTP 요청 자체는 성공해도, 응답 body 안에서 상품주문번호별 성공/실패가 나뉠 수 있습니다.

n8n에서는 Lambda 응답의 `ok`만 보지 말고, 네이버 원본 응답 안의 성공/실패 목록도 확인해야 합니다.

일반적으로 확인할 값:

| 값 | 의미 |
| --- | --- |
| `data.successProductOrderIds` | 네이버가 성공 처리한 상품주문번호 목록 |
| `data.failProductOrderInfos` | 네이버가 실패 처리한 상품주문번호와 실패 사유 목록 |
| `meta.naverStatusCode` | 네이버 HTTP 상태 코드 |
| `meta.naverTraceId` | 네이버 문의 또는 로그 추적용 ID |

권장 n8n 처리:

```text
1. ok = false
   -> 담당자 알림

2. ok = true 이지만 failProductOrderInfos가 있음
   -> 부분 실패로 보고 실패 건만 담당자 알림 또는 재처리 큐로 분기

3. ok = true 이고 successProductOrderIds만 있음
   -> 성공 처리
```

## 공통 코드값

아래 코드는 자주 쓰는 값만 정리합니다. 현재 택배사가 고정되어 있으므로, 1차 구현에서는 택배사 코드 조회 API를 별도로 구현하지 않습니다.

### 배송 방법

| 값 | 의미 | 주 사용처 |
| --- | --- | --- |
| `DELIVERY` | 택배, 등기, 소포 | 일반 발송, 교환 재배송 |
| `VISIT_RECEIPT` | 방문 수령 | 직접 수령 |
| `DIRECT_DELIVERY` | 직접 전달 | 직접 배송 |
| `QUICK_SVC` | 퀵서비스 | 퀵 배송 |
| `NOTHING` | 배송 없음 | 배송 없는 상품 |
| `RETURN_DESIGNATED` | 지정 반품 택배 | 반품 수거 |
| `RETURN_DELIVERY` | 일반 반품 택배 | 반품 수거 |
| `RETURN_INDIVIDUAL` | 직접 반송 | 반품 수거 |

### 자주 쓰는 택배사 코드

| 값 | 의미 |
| --- | --- |
| `HANJIN` | 한진택배 |
| `CJGLS` | CJ대한통운 |
| `HYUNDAI` | 롯데택배 |
| `KGB` | 로젠택배 |
| `EPOST` | 우체국택배 |

### 보류 유형

교환과 반품 보류에서 공통으로 쓰입니다.

| 값 | 의미 |
| --- | --- |
| `RETURN_DELIVERYFEE` | 반품 배송비 청구 |
| `EXTRAFEEE` | 추가 비용 청구 |
| `RETURN_DELIVERYFEE_AND_EXTRAFEEE` | 반품 배송비 + 추가 비용 청구 |
| `RETURN_PRODUCT_NOT_DELIVERED` | 반품 상품 미입고 |
| `EXCHANGE_DELIVERYFEE` | 교환 배송비 청구 |
| `EXCHANGE_EXTRAFEE` | 추가 교환 비용 청구 |
| `EXCHANGE_PRODUCT_READY` | 교환 상품 준비 중 |
| `EXCHANGE_PRODUCT_NOT_DELIVERED` | 교환 상품 미입고 |
| `EXCHANGE_HOLDBACK` | 교환 구매 확정 보류 |
| `SELLER_CONFIRM_NEED` | 판매자 확인 필요 |
| `PURCHASER_CONFIRM_NEED` | 구매자 확인 필요 |
| `SELLER_REMIT` | 판매자 직접 송금 |
| `ETC` | 기타 사유 |
| `ETC2` | 기타 |

## Operation 목록

| operation | Method | Naver endpoint | 목적 |
| --- | --- | --- | --- |
| `order.getProductOrderIds` | GET | `/v1/pay-order/seller/orders/{orderId}/product-order-ids` | 주문번호로 상품주문번호 목록 조회 |
| `order.getChangedOrders` | GET | `/v1/pay-order/seller/product-orders/last-changed-statuses` | 변경된 상품주문 목록 조회 |
| `order.searchByCondition` | GET | `/v1/pay-order/seller/product-orders` | 조건 기반 상품주문 상세 목록 조회 |
| `order.getDetails` | POST | `/v1/pay-order/seller/product-orders/query` | 상품주문번호 배열로 상세 조회 |
| `order.confirm` | POST | `/v1/pay-order/seller/product-orders/confirm` | 발주 확인 처리 |
| `product.getOriginProduct` | GET | `/v2/products/origin-products/{originProductNo}` | 원상품 정보 조회 |
| `product.getChannelProduct` | GET | `/v2/products/channel-products/{channelProductNo}` | 채널 상품 정보 조회 |
| `delivery.dispatch` | POST | `/v1/pay-order/seller/product-orders/dispatch` | 발송 처리 |
| `delivery.delayDispatch` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/delay` | 발송 지연 처리 |
| `delivery.changeHopeDelivery` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/hope-delivery/change` | 배송 희망일 변경 |
| `exchange.collectApprove` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/collect/approve` | 교환 수거 완료 |
| `exchange.redispatch` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/dispatch` | 교환 재배송 처리 |
| `exchange.hold` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/holdback` | 교환 보류 |
| `exchange.releaseHold` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/holdback/release` | 교환 보류 해제 |
| `exchange.reject` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/reject` | 교환 거부 또는 철회 |
| `return.request` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/return/request` | 반품 요청 |
| `return.approve` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/return/approve` | 반품 승인 |
| `return.hold` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/return/holdback` | 반품 보류 |
| `return.releaseHold` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/return/holdback/release` | 반품 보류 해제 |
| `return.reject` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/return/reject` | 반품 거부 또는 철회 |
| `cancel.request` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/cancel/request` | 취소 요청 |
| `cancel.approve` | POST | `/v1/pay-order/seller/product-orders/{productOrderId}/claim/cancel/approve` | 취소 요청 승인 |

## 어떤 operation을 써야 하나요?

아래 표는 n8n 사용자가 작업 상황에 맞는 operation을 고를 때 사용합니다.

| 하고 싶은 일 | 사용할 operation | 설명 |
| --- | --- | --- |
| 주문번호만 있고 상품주문번호가 없을 때 | `order.getProductOrderIds` | 네이버 후속 처리는 대부분 상품주문번호 기준이므로, 주문번호를 상품주문번호로 변환합니다. |
| 최근 결제완료, 발송완료, 클레임 변경 건을 모으고 싶을 때 | `order.getChangedOrders` | 일정 시간 범위 안에서 변경된 상품주문을 가져옵니다. 주기적 동기화나 신규 주문 감지에 적합합니다. |
| 특정 조건의 주문 목록을 한 번에 보고 싶을 때 | `order.searchByCondition` | 결제일, 주문상태, 클레임상태 같은 조건으로 현재 상태 기준의 주문 목록을 조회합니다. |
| 상품주문번호의 상세 정보가 필요할 때 | `order.getDetails` | 주문자, 수취인, 배송지, 상품, 배송, 클레임 상세 정보를 확인합니다. |
| 결제완료 주문을 발주 확인 처리하고 싶을 때 | `order.confirm` | 상품주문을 발주 확인 상태로 변경합니다. 보통 신규 결제 주문 조회 후 호출합니다. |
| 상품에 설정한 판매자 관리 코드나 옵션별 품번을 확인하고 싶을 때 | `product.getOriginProduct` | 주문 상세의 `originalProductId`로 원상품을 조회합니다. 옵션별 `sellerManagerCode` 확인에 사용합니다. |
| 네이버 채널 상품 단위의 상품 정보를 확인하고 싶을 때 | `product.getChannelProduct` | 주문 상세의 `productId`로 채널 상품을 조회합니다. 원상품 조회만으로 부족할 때 보조로 사용합니다. |
| 송장번호를 넣어 발송 처리하고 싶을 때 | `delivery.dispatch` | 택배사, 송장번호, 발송일시를 네이버에 등록합니다. |
| 직접 전달로 발송 처리하고 싶을 때 | `delivery.dispatch` | 배송 방법을 `DIRECT_DELIVERY`로 보내고 송장번호 없이 발송 처리합니다. |
| 발송이 늦어져 기한을 연장해야 할 때 | `delivery.delayDispatch` | 발송 지연 사유와 새 발송 기한을 등록합니다. |
| 고객 요청 등으로 배송 희망일을 바꿔야 할 때 | `delivery.changeHopeDelivery` | 희망 배송일과 변경 사유를 등록합니다. 일반 발송보다 사용 빈도는 낮습니다. |
| 교환 상품이 회수되었음을 처리하고 싶을 때 | `exchange.collectApprove` | 교환 수거 완료 상태로 넘깁니다. |
| 교환 상품을 새 송장으로 다시 보내고 싶을 때 | `exchange.redispatch` | 교환 재배송 송장 정보를 등록합니다. |
| 교환 상품을 직접 전달로 다시 보내고 싶을 때 | `exchange.redispatch` | 재배송 방법을 `DIRECT_DELIVERY`로 보내고 송장번호 없이 처리합니다. |
| 교환 처리를 잠시 멈춰야 할 때 | `exchange.hold` | 미입고, 추가 비용, 확인 필요 등으로 교환을 보류합니다. |
| 교환 보류를 풀고 다음 처리를 진행하고 싶을 때 | `exchange.releaseHold` | 기존 교환 보류 상태를 해제합니다. |
| 교환 요청을 거부하거나 철회해야 할 때 | `exchange.reject` | 교환 거부 또는 철회 사유를 등록합니다. |
| 판매자가 반품 요청을 새로 만들 때 | `return.request` | 발송 이후 주문에 대해 반품 클레임을 생성합니다. |
| 반품 상품 확인 후 환불을 확정하고 싶을 때 | `return.approve` | 반품을 승인합니다. |
| 반품 상품 미입고, 배송비 청구 등으로 처리를 멈출 때 | `return.hold` | 반품을 보류합니다. |
| 반품 보류를 풀고 승인/거부 등 다음 단계로 갈 때 | `return.releaseHold` | 반품 보류 상태를 해제합니다. |
| 반품 요청을 거부하거나 철회해야 할 때 | `return.reject` | 반품 거부 또는 철회 사유를 등록합니다. |
| 판매자가 취소 요청을 만들 때 | `cancel.request` | 발송 전 주문에 대해 취소 클레임을 생성합니다. |
| 구매자 또는 판매자 취소 요청을 승인할 때 | `cancel.approve` | 취소 요청을 승인합니다. |

## 대표 n8n 흐름

### 신규 결제 주문 발주 확인

```text
1. Cron 노드
2. order.getChangedOrders
   - lastChangedType = PAYED
3. order.getDetails
   - 필요한 주문/배송/상품 정보 확인
4. n8n IF 또는 Code 노드
   - 발주 확인 대상만 필터링
5. order.confirm
6. 성공/실패 결과 기록
```

이 흐름에서는 `order.getChangedOrders`가 "변경된 주문 찾기", `order.getDetails`가 "상세 정보 확인", `order.confirm`이 "상태 변경" 역할을 합니다.

### 송장 입력 후 발송 처리

```text
1. 시트 또는 DB에서 송장 입력 완료 행 조회
2. delivery.dispatch
3. 응답의 successProductOrderIds, failProductOrderInfos 확인
4. 성공 행은 발송 완료로 표시
5. 실패 행은 담당자 알림 또는 재처리 대상으로 표시
```

송장번호, 택배사 코드, 상품주문번호가 이미 준비되어 있으면 `order.getDetails` 없이 `delivery.dispatch`를 바로 호출해도 됩니다.
직접 전달은 송장번호 없이 `deliveryMethod`를 `DIRECT_DELIVERY`로 보내면 됩니다.

### 교환 재배송 처리

```text
1. 교환 대상 행 조회
2. 필요하면 order.getDetails로 현재 클레임 정보 확인
3. exchange.redispatch
4. n8n에서 새 송장 정보 또는 처리 결과 기록
```

Lambda는 복잡한 교환 상태 판단을 하지 않습니다. 교환 대상인지 판단하는 업무 로직은 n8n에서 처리합니다.
교환 재배송도 직접 전달이면 `reDeliveryMethod`를 `DIRECT_DELIVERY`로 보내고 재배송 택배사/송장번호는 생략합니다.

### 반품 승인 처리

```text
1. 반품 입고 완료 대상 조회
2. return.approve
3. 실패 시 네이버 원본 메시지와 traceId를 담당자에게 알림
```

반품 보류가 필요한 경우에는 `return.hold`를 먼저 사용하고, 보류가 해결되면 `return.releaseHold` 후 `return.approve`를 사용합니다.

### 취소 처리

```text
1. 취소 대상 주문 확인
2. cancel.request 또는 cancel.approve 선택
3. 처리 결과 기록
```

판매자가 새로 취소를 요청하는 경우는 `cancel.request`, 이미 들어온 취소 요청을 승인하는 경우는 `cancel.approve`를 사용합니다.

## 주문 조회

### `order.getProductOrderIds`

주문번호 `orderId`에 속한 상품주문번호 목록을 조회합니다.

사용 시점:

- n8n에 `orderId`만 있고 `productOrderId`가 없을 때 사용합니다.
- 발주 확인, 발송, 취소, 반품, 교환은 대부분 `productOrderId` 기준이므로 후속 처리를 하기 전에 이 operation으로 변환합니다.

사용하지 않아도 되는 경우:

- 이미 n8n 데이터에 `productOrderId`가 있으면 바로 후속 operation을 호출합니다.

```text
GET /v1/pay-order/seller/orders/{orderId}/product-order-ids
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `orderId` | string | 주문 번호 |

예시:

```json
{
  "operation": "order.getProductOrderIds",
  "payload": {
    "orderId": "2026051912345678"
  }
}
```

### `order.getChangedOrders`

지정한 기간에 변경된 상품주문 목록을 조회합니다.

사용 시점:

- 신규 결제 주문을 주기적으로 찾고 싶을 때 사용합니다.
- 배송완료, 취소, 반품, 교환 등 상태 변경분을 동기화하고 싶을 때 사용합니다.
- "마지막 실행 이후 바뀐 주문만 가져오기" 같은 폴링 흐름에 적합합니다.

주의:

- 응답은 상세 주문 정보가 아니라 변경된 상품주문 식별자 중심입니다.
- 상세 정보가 필요하면 응답에서 `productOrderId`를 모아 `order.getDetails`를 이어서 호출합니다.
- 응답에 `more` 정보가 있으면 `moreSequence`를 사용해 다음 목록을 이어서 조회해야 합니다.

```text
GET /v1/pay-order/seller/product-orders/last-changed-statuses
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `lastChangedFrom` | string(date-time) | 조회 시작 일시 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `lastChangedTo` | string(date-time) | 조회 종료 일시. 생략 시 시작일시부터 24시간 |
| `lastChangedType` | string | 최종 변경 구분 |
| `moreSequence` | string | 추가 페이지 조회용 sequence |
| `limitCount` | integer | 최대 조회 건수. 최대 300 |

예시:

```json
{
  "operation": "order.getChangedOrders",
  "payload": {
    "lastChangedFrom": "2026-05-19T00:00:00.000+09:00",
    "lastChangedTo": "2026-05-19T23:59:59.999+09:00",
    "lastChangedType": "PAYED",
    "limitCount": 300
  }
}
```

### `order.searchByCondition`

시간, 주문상태, 클레임상태 조건으로 상품주문 상세 목록을 조회합니다.

사용 시점:

- 특정 기간의 결제완료 주문, 발주 대기 주문, 클레임 진행 주문을 조건으로 조회하고 싶을 때 사용합니다.
- "현재 상태 기준으로 업무 큐 만들기"에 적합합니다.

`order.getChangedOrders`와 차이:

- `order.getChangedOrders`는 변경 이력 기반 조회입니다. 주기적 동기화에 적합합니다.
- `order.searchByCondition`은 현재 조건 기반 조회입니다. 특정 상태의 목록을 한 번에 보고 싶을 때 적합합니다.

주의:

- 결과가 많으면 `page`, `pageSize`로 페이지를 넘겨야 합니다.
- 페이지를 넘기는 동안 주문 상태가 바뀔 수 있으므로, 정밀한 동기화는 `order.getChangedOrders`가 더 안전합니다.

```text
GET /v1/pay-order/seller/product-orders
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `from` | string(date-time) | 조회 기준 시작 일시 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `to` | string(date-time) | 조회 기준 종료 일시 |
| `rangeType` | string | 조회 일시 기준 |
| `productOrderStatuses` | array | 상품주문 상태 목록 |
| `claimStatuses` | array | 클레임 상태 목록 |
| `placeOrderStatusType` | string | 발주 상태 유형 |
| `fulfillment` | boolean | 풀필먼트 배송 여부 |
| `pageSize` | integer | 페이지 크기. 1~300 |
| `page` | integer | 페이지 번호. 1부터 시작 |
| `quantityClaimCompatibility` | boolean | 수량 클레임 호환 여부 |

예시:

```json
{
  "operation": "order.searchByCondition",
  "payload": {
    "from": "2026-05-19T00:00:00.000+09:00",
    "to": "2026-05-19T23:59:59.999+09:00",
    "rangeType": "PAYED_DATETIME",
    "productOrderStatuses": ["PAYED"],
    "placeOrderStatusType": "NOT_YET",
    "page": 1,
    "pageSize": 100,
    "quantityClaimCompatibility": true
  }
}
```

### `order.getDetails`

상품주문번호 배열로 상세 주문, 배송, 클레임 정보를 조회합니다.

사용 시점:

- 상품주문번호만 있고 주문자, 수취인, 배송지, 상품명, 클레임 상태 등 상세 정보가 필요할 때 사용합니다.
- `order.getChangedOrders` 다음 단계에서 상세 정보를 채우는 용도로 자주 사용합니다.
- 고객 정보는 별도 고객 조회 API가 아니라 이 주문 상세 응답 안에서 확인합니다.

주의:

- 개인정보가 포함될 수 있으므로 n8n 로그, 알림, 시트 저장 범위를 신중히 정해야 합니다.
- Lambda 로그에는 전화번호, 상세주소 같은 값을 남기지 않습니다.

```text
POST /v1/pay-order/seller/product-orders/query
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderIds` | array | 상품주문번호 목록 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `quantityClaimCompatibility` | boolean | 수량 클레임 호환 여부 |

예시:

```json
{
  "operation": "order.getDetails",
  "payload": {
    "productOrderIds": ["1234567890", "1234567891"],
    "quantityClaimCompatibility": true
  }
}
```

## 상품 조회

### `product.getOriginProduct`

원상품 번호로 상품 정보를 조회합니다.

사용 시점:

- 주문 상세의 `productOrder.originalProductId`를 기준으로 상품에 설정한 판매자 관리 코드, 내부 코드, 옵션별 관리 코드를 확인할 때 사용합니다.
- 주문 상세 응답에 `sellerProductCode`, `optionManageCode`, `sellerCustomCode1`, `sellerCustomCode2`가 내려오지 않을 때 상품 정보에서 품번을 보강할 수 있습니다.
- 조합형 옵션상품의 옵션별 품번은 원상품 응답의 `optionInfo.optionCombinations[].sellerManagerCode`에 있을 수 있습니다.

주의:

- 주문 상세의 `productOrder.originalProductId` 값을 `originProductNo`로 보냅니다.
- 응답 구조는 상품 유형과 옵션 설정 방식에 따라 달라질 수 있으므로, n8n에서 `optionInfo` 하위 값을 확인해 매칭해야 합니다.

```text
GET /v2/products/origin-products/{originProductNo}
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `originProductNo` | string | 원상품 번호. 주문 상세의 `productOrder.originalProductId` |

예시:

```json
{
  "operation": "product.getOriginProduct",
  "payload": {
    "originProductNo": "9622953632"
  }
}
```

### `product.getChannelProduct`

채널 상품 번호로 상품 정보를 조회합니다.

사용 시점:

- 주문 상세의 `productOrder.productId` 기준으로 채널 상품 정보를 확인할 때 사용합니다.
- 원상품 조회만으로 필요한 상품 코드가 확인되지 않을 때 보조 조회로 사용합니다.

주의:

- 주문 상세의 `productOrder.productId` 값을 `channelProductNo`로 보냅니다.

```text
GET /v2/products/channel-products/{channelProductNo}
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `channelProductNo` | string | 채널 상품 번호. 주문 상세의 `productOrder.productId` |

예시:

```json
{
  "operation": "product.getChannelProduct",
  "payload": {
    "channelProductNo": "9669003478"
  }
}
```

## 발주/배송

### `order.confirm`

상품주문을 발주 확인 처리합니다.

사용 시점:

- 결제완료 주문을 판매자가 확인했다는 상태로 넘길 때 사용합니다.
- 신규 주문 자동 확인 플로우의 마지막 단계로 자주 사용합니다.

주의:

- 이미 발주 확인되었거나 상태 전이가 불가능한 주문은 네이버에서 실패할 수 있습니다.
- Lambda는 주문 상태를 미리 판단하지 않고 네이버 응답을 표준 형식으로 전달합니다.
- 대량 처리 시 n8n에서 30개 이하 단위로 나누는 것을 권장합니다.

```text
POST /v1/pay-order/seller/product-orders/confirm
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderIds` | array | 상품주문번호 목록. Adapter에서는 최대 30개 단위 사용을 권장 |

예시:

```json
{
  "operation": "order.confirm",
  "payload": {
    "productOrderIds": ["1234567890", "1234567891"]
  }
}
```

### `delivery.dispatch`

상품주문을 발송 처리합니다.

사용 시점:

- 송장번호가 확정된 주문을 네이버에 발송 처리할 때 사용합니다.
- 직접 전달 주문은 송장번호 없이 발송 처리할 때 사용합니다.
- 기존 `handleOrderComplete_naver` Lambda가 하던 발송 처리 역할을 이 operation으로 대체할 수 있습니다.

주의:

- `deliveryMethod`가 `DELIVERY`이면 `deliveryCompanyCode`는 네이버가 허용하는 택배사 코드여야 합니다.
- `deliveryMethod`가 `DELIVERY`이면 `trackingNumber`가 필요합니다.
- `deliveryMethod`가 `DIRECT_DELIVERY`이면 `deliveryCompanyCode`, `trackingNumber`는 보내지 않아도 됩니다.
- 이미 발송된 주문이거나 상태 전이가 불가능한 주문이면 네이버에서 실패할 수 있습니다.
- 응답에서 상품주문번호별 성공/실패 목록을 확인해야 합니다.

```text
POST /v1/pay-order/seller/product-orders/dispatch
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `dispatchProductOrders` | array | 발송 처리 대상 목록 |
| `dispatchProductOrders[].productOrderId` | string | 상품주문번호 |
| `dispatchProductOrders[].deliveryMethod` | string | 배송 방법. 일반 택배는 `DELIVERY`, 직접 전달은 `DIRECT_DELIVERY` |
| `dispatchProductOrders[].dispatchDate` | string(date-time) | 발송일시 |

조건부 필수 payload:

| 조건 | 필수 필드 | 설명 |
| --- | --- | --- |
| `deliveryMethod = DELIVERY` | `dispatchProductOrders[].deliveryCompanyCode` | 택배사 코드. 예: `HANJIN` |
| `deliveryMethod = DELIVERY` | `dispatchProductOrders[].trackingNumber` | 송장번호 |

일반 택배 예시:

```json
{
  "operation": "delivery.dispatch",
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

직접 전달 예시:

```json
{
  "operation": "delivery.dispatch",
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

### `delivery.delayDispatch`

발송 지연 사유와 발송 예정일을 등록합니다.

사용 시점:

- 발주 확인은 되었지만 재고, 고객 요청, 주문 제작 등으로 발송 기한을 지키기 어려울 때 사용합니다.
- 자동 취소나 클레임으로 이어지기 전에 지연 사유를 남기는 용도입니다.

주의:

- 실제 사용 시 `dispatchDueDate`와 `delayedDispatchReason`은 사실상 필수로 봅니다.
- 지연 처리 가능 상태가 아니면 네이버에서 실패할 수 있습니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/delay
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `dispatchDueDate` | string(date-time) | 발송 기한 |
| `delayedDispatchReason` | string | 발송 지연 사유 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `dispatchDelayedDetailedReason` | string | 발송 지연 상세 사유 |

주요 `delayedDispatchReason` 값:

| 값 | 의미 |
| --- | --- |
| `PRODUCT_PREPARE` | 상품 준비 중 |
| `CUSTOMER_REQUEST` | 고객 요청 |
| `CUSTOM_BUILD` | 주문 제작 |
| `RESERVED_DISPATCH` | 예약 발송 |
| `OVERSEA_DELIVERY` | 해외 배송 |
| `ETC` | 기타 |

예시:

```json
{
  "operation": "delivery.delayDispatch",
  "payload": {
    "productOrderId": "1234567890",
    "dispatchDueDate": "2026-05-21T18:00:00.000+09:00",
    "delayedDispatchReason": "PRODUCT_PREPARE",
    "dispatchDelayedDetailedReason": "재고 입고 후 발송 예정"
  }
}
```

### `delivery.changeHopeDelivery`

배송 희망일을 변경합니다.

사용 시점:

- 고객 요청 또는 운영 사유로 배송 희망일을 바꿔야 할 때 사용합니다.
- 일반 발송 플로우보다는 희망일 배송 상품을 다룰 때 사용합니다.

주의:

- `hopeDeliveryYmd`는 `yyyyMMdd` 형식입니다.
- 일반 택배 발송 처리에는 보통 `delivery.dispatch`를 사용합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/hope-delivery/change
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `hopeDeliveryYmd` | string | 배송 희망일. `yyyyMMdd` |
| `changeReason` | string | 변경 사유 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `hopeDeliveryHm` | string | 배송 희망 시간. `HHmm` |
| `region` | string | 지역 |

예시:

```json
{
  "operation": "delivery.changeHopeDelivery",
  "payload": {
    "productOrderId": "1234567890",
    "hopeDeliveryYmd": "20260521",
    "hopeDeliveryHm": "1400",
    "region": "서울",
    "changeReason": "고객 요청"
  }
}
```

## 교환

### `exchange.collectApprove`

교환 수거 완료 처리합니다.

사용 시점:

- 구매자가 보낸 교환 상품이 회수되었고, 네이버에 수거 완료 상태를 반영해야 할 때 사용합니다.
- 이후 교환 재배송을 진행하기 전에 사용할 수 있습니다.

주의:

- 실제 교환 클레임 상태가 수거 완료 처리 가능한 상태여야 합니다.
- 상태가 맞지 않으면 네이버에서 실패하며, Lambda는 그 실패 사유를 전달합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/collect/approve
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |

예시:

```json
{
  "operation": "exchange.collectApprove",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

### `exchange.redispatch`

교환 상품을 재배송 처리합니다.

사용 시점:

- 교환 상품을 새 송장으로 다시 발송할 때 사용합니다.
- 교환 상품을 직접 전달로 다시 처리할 때도 사용합니다.
- AS/교환 처리 플로우에서 가장 자주 쓰일 가능성이 높은 교환 operation입니다.

주의:

- 이 operation은 네이버 교환 클레임의 재배송 처리입니다.
- `reDeliveryMethod`가 `DELIVERY`이면 `reDeliveryCompany`, `reDeliveryTrackingNumber`가 필요합니다.
- `reDeliveryMethod`가 `DIRECT_DELIVERY`이면 재배송 택배사/송장번호를 보내지 않아도 됩니다.
- n8n 내부에서 "새 배송 행 생성"이 필요하면, 그 행 생성은 n8n 또는 DB/시트 쪽에서 처리합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/dispatch
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `reDeliveryMethod` | string | 재배송 방법. 일반 택배는 `DELIVERY`, 직접 전달은 `DIRECT_DELIVERY` |

조건부 필수 payload:

| 조건 | 필수 필드 | 설명 |
| --- | --- | --- |
| `reDeliveryMethod = DELIVERY` | `reDeliveryCompany` | 재배송 택배사 코드. 예: `HANJIN` |
| `reDeliveryMethod = DELIVERY` | `reDeliveryTrackingNumber` | 재배송 송장번호 |

일반 택배 예시:

```json
{
  "operation": "exchange.redispatch",
  "payload": {
    "productOrderId": "1234567890",
    "reDeliveryMethod": "DELIVERY",
    "reDeliveryCompany": "HANJIN",
    "reDeliveryTrackingNumber": "111122223333"
  }
}
```

직접 전달 예시:

```json
{
  "operation": "exchange.redispatch",
  "payload": {
    "productOrderId": "1234567890",
    "reDeliveryMethod": "DIRECT_DELIVERY"
  }
}
```

### `exchange.hold`

교환을 보류 처리합니다.

사용 시점:

- 교환 상품이 아직 입고되지 않았거나, 추가 비용 확인이 필요하거나, 판매자/구매자 확인이 필요한 경우 사용합니다.
- 교환 처리를 바로 진행하지 않고 멈춰야 할 때 사용합니다.

주의:

- 보류 사유는 담당자가 봐도 이해할 수 있게 `holdbackExchangeDetailReason`에 구체적으로 작성합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/holdback
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `holdbackClassType` | string | 보류 유형 |
| `holdbackExchangeDetailReason` | string | 보류 상세 사유 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `extraExchangeFeeAmount` | number | 기타 교환 비용 |

예시:

```json
{
  "operation": "exchange.hold",
  "payload": {
    "productOrderId": "1234567890",
    "holdbackClassType": "EXCHANGE_PRODUCT_NOT_DELIVERED",
    "holdbackExchangeDetailReason": "교환 수거 상품 미입고"
  }
}
```

### `exchange.releaseHold`

교환 보류를 해제합니다.

사용 시점:

- 교환 보류 사유가 해결되어 다시 처리를 진행할 때 사용합니다.
- 보류 해제 후 필요에 따라 `exchange.redispatch` 또는 다른 교환 처리를 이어서 호출합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/holdback/release
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |

예시:

```json
{
  "operation": "exchange.releaseHold",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

### `exchange.reject`

교환을 거부 또는 철회 처리합니다.

사용 시점:

- 교환 요청을 받아들일 수 없거나, 구매자 요청으로 교환이 철회되는 경우 사용합니다.

주의:

- `rejectExchangeReason`은 담당자와 고객이 이해할 수 있는 수준으로 작성합니다.
- 실제 고객 안내 문구로 활용될 수 있으므로 짧고 명확하게 작성합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/exchange/reject
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `rejectExchangeReason` | string | 교환 거부 또는 철회 사유 |

예시:

```json
{
  "operation": "exchange.reject",
  "payload": {
    "productOrderId": "1234567890",
    "rejectExchangeReason": "고객 요청으로 교환 철회"
  }
}
```

## 반품

### `return.request`

판매자 반품 요청을 생성합니다.

사용 시점:

- 판매자 주도로 반품 클레임을 만들어야 할 때 사용합니다.
- 발송 이후 상품에 대해 반품 수거 방법과 반품 사유를 등록합니다.

주의:

- 구매자가 이미 반품을 신청한 건을 승인하는 작업은 `return.approve`입니다.
- 이 operation은 "반품 요청 생성"이고, 환불 확정은 아닙니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/return/request
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `returnReason` | string | 반품 사유 |
| `collectDeliveryMethod` | string | 수거 배송 방법 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `collectDeliveryCompany` | string | 수거 택배사 코드 |
| `collectTrackingNumber` | string | 수거 송장번호 |
| `returnQuantity` | integer | 반품 수량. 생략 시 전체 수량 |

주요 `returnReason` 값:

| 값 | 의미 |
| --- | --- |
| `INTENT_CHANGED` | 구매 의사 취소 |
| `COLOR_AND_SIZE` | 색상 및 사이즈 변경 |
| `WRONG_ORDER` | 다른 상품 잘못 주문 |
| `PRODUCT_UNSATISFIED` | 서비스 불만족 |
| `DELAYED_DELIVERY` | 배송 지연 |
| `SOLD_OUT` | 상품 품절 |
| `DROPPED_DELIVERY` | 배송 누락 |
| `BROKEN` | 상품 파손 |
| `INCORRECT_INFO` | 상품 정보 상이 |
| `WRONG_DELIVERY` | 오배송 |
| `WRONG_OPTION` | 색상 등 다른 상품 잘못 배송 |

예시:

```json
{
  "operation": "return.request",
  "payload": {
    "productOrderId": "1234567890",
    "returnReason": "WRONG_OPTION",
    "collectDeliveryMethod": "RETURN_DESIGNATED",
    "collectDeliveryCompany": "HANJIN",
    "collectTrackingNumber": "111122223333",
    "returnQuantity": 1
  }
}
```

### `return.approve`

반품을 승인합니다.

사용 시점:

- 반품 상품 입고와 검수가 끝났고 환불을 확정해도 되는 경우 사용합니다.

주의:

- 반품 보류 상태이면 먼저 `return.releaseHold`가 필요할 수 있습니다.
- Lambda는 상태를 미리 판단하지 않으므로 네이버 실패 응답을 확인합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/return/approve
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |

예시:

```json
{
  "operation": "return.approve",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

### `return.hold`

반품을 보류 처리합니다.

사용 시점:

- 반품 상품 미입고, 배송비 청구, 추가 확인 필요 등으로 반품 승인을 미뤄야 할 때 사용합니다.

주의:

- `holdbackReturnDetailReason`에는 담당자가 후속 조치를 알 수 있도록 구체적인 사유를 작성합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/return/holdback
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `holdbackClassType` | string | 보류 유형 |
| `holdbackReturnDetailReason` | string | 보류 상세 사유 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `extraReturnFeeAmount` | number | 기타 반품 비용 |

예시:

```json
{
  "operation": "return.hold",
  "payload": {
    "productOrderId": "1234567890",
    "holdbackClassType": "RETURN_PRODUCT_NOT_DELIVERED",
    "holdbackReturnDetailReason": "반품 상품 미입고"
  }
}
```

### `return.releaseHold`

반품 보류를 해제합니다.

사용 시점:

- 반품 보류 사유가 해결되어 승인 또는 거부 같은 다음 처리를 진행할 때 사용합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/return/holdback/release
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |

예시:

```json
{
  "operation": "return.releaseHold",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

### `return.reject`

반품을 거부 또는 철회 처리합니다.

사용 시점:

- 반품 사유가 인정되지 않거나, 구매자 요청으로 반품이 철회되는 경우 사용합니다.

주의:

- `rejectReturnReason`은 사후 분쟁 대응에도 쓰일 수 있으므로 명확하게 작성합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/return/reject
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `rejectReturnReason` | string | 반품 거부 또는 철회 사유 |

예시:

```json
{
  "operation": "return.reject",
  "payload": {
    "productOrderId": "1234567890",
    "rejectReturnReason": "고객 요청으로 반품 철회"
  }
}
```

## 취소

### `cancel.request`

판매자 취소 요청을 생성합니다.

사용 시점:

- 판매자가 품절, 오주문, 고객 요청 등으로 취소 요청을 시작해야 할 때 사용합니다.
- 보통 발송 전 주문에 사용합니다.

주의:

- 이미 구매자가 취소 요청을 넣은 건을 승인하는 경우는 `cancel.approve`를 사용합니다.
- 부분 취소가 필요한 경우 `cancelQuantity`를 사용합니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/cancel/request
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |
| `cancelReason` | string | 취소 사유 |

선택 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `cancelDetailedReason` | string | 취소 상세 사유 |
| `cancelQuantity` | integer | 취소 수량. 생략 시 전체 수량 |

주요 `cancelReason` 값:

| 값 | 의미 |
| --- | --- |
| `INTENT_CHANGED` | 구매 의사 취소 |
| `COLOR_AND_SIZE` | 색상 및 사이즈 변경 |
| `WRONG_ORDER` | 다른 상품 잘못 주문 |
| `PRODUCT_UNSATISFIED` | 서비스 불만족 |
| `DELAYED_DELIVERY` | 배송 지연 |
| `SOLD_OUT` | 상품 품절 |
| `INCORRECT_INFO` | 상품 정보 상이 |

예시:

```json
{
  "operation": "cancel.request",
  "payload": {
    "productOrderId": "1234567890",
    "cancelReason": "SOLD_OUT",
    "cancelDetailedReason": "재고 부족",
    "cancelQuantity": 1
  }
}
```

### `cancel.approve`

취소 요청을 승인합니다.

사용 시점:

- 구매자 또는 시스템에 의해 들어온 취소 요청을 판매자가 승인할 때 사용합니다.

주의:

- 판매자가 새로 취소를 만들고 싶다면 `cancel.request`를 사용합니다.
- 취소 승인 가능 상태가 아니면 네이버에서 실패할 수 있습니다.

```text
POST /v1/pay-order/seller/product-orders/{productOrderId}/claim/cancel/approve
```

필수 payload:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `productOrderId` | string | 상품주문번호 |

예시:

```json
{
  "operation": "cancel.approve",
  "payload": {
    "productOrderId": "1234567890"
  }
}
```

## 구현 보류 operation

아래 operation은 추후 필요해질 때 구현합니다.

| operation | Method | Naver endpoint | 필수 payload | 보류 이유 |
| --- | --- | --- | --- | --- |
| `product.search` | POST | `/v1/products/search` | 없음 | 상품 운영 자동화가 필요해질 때 추가 |
| `product.changeStatus` | PUT | `/v1/products/origin-products/{originProductNo}/change-status` | `originProductNo`, `statusType` | 판매 상태 자동화 필요 시 추가 |
| `product.updateOptionStock` | PUT | `/v1/products/origin-products/{originProductNo}/option-stock` | `originProductNo`, `optionInfo` | 재고 자동화 정책 확정 후 추가 |
| `qna.listCustomerInquiries` | GET | `/v1/pay-user/inquiries` | `startSearchDate`, `endSearchDate` | 문의 처리 자동화가 필요해질 때 추가 |
| `qna.listProductQnas` | GET | `/v1/contents/qnas` | `fromDate`, `toDate` | 상품 문의 자동화가 필요해질 때 추가 |
| `qna.answerProductQna` | PUT | `/v1/contents/qnas/{questionId}` | `questionId`, `commentContent` | 답변 템플릿/검수 정책 확정 후 추가 |
| `seller.getAccount` | GET | `/v1/seller/account` | 없음 | 초기 연결 확인용. 상시 업무 필요성 낮음 |
| `seller.getChannels` | GET | `/v1/seller/channels` | 없음 | 초기 연결 확인용. 상시 업무 필요성 낮음 |
| `seller.getLogisticsCompanies` | GET | `/v1/logistics/logistics-companies` | 없음 | 연동 물류사 설정 확인용. 현재 택배사가 고정이라 1차 필수 아님 |
| `seller.getWarehouses` | GET | `/v1/logistics/outbound-locations` | 없음 | 출고지/창고 자동 분기 필요 시 추가 |
| `delivery.getReturnDeliveryCompanies` | GET | `/v2/product-delivery-info/return-delivery-companies` | 없음 | 반품/교환 택배사 코드 목록 확인용. 수거 송장번호 조회용은 아님 |

## 라우팅 구현 기준

`naver-commerce-api` 내부에는 명시적인 operation catalog를 둡니다.

각 operation은 다음 정보를 가져야 합니다.

```text
operation
method
path
pathParams
queryParams
bodyFields
requiredFields
conditionalRequired
payloadTransform
```

예:

```json
{
  "operation": "delivery.dispatch",
  "method": "POST",
  "path": "/v1/pay-order/seller/product-orders/dispatch",
  "requiredFields": [
    "dispatchProductOrders",
    "dispatchProductOrders[].productOrderId",
    "dispatchProductOrders[].deliveryMethod",
    "dispatchProductOrders[].dispatchDate"
  ],
  "conditionalRequired": [
    {
      "path": "dispatchProductOrders[]",
      "when": {
        "field": "deliveryMethod",
        "equals": "DELIVERY"
      },
      "required": [
        "deliveryCompanyCode",
        "trackingNumber"
      ]
    }
  ]
}
```

구현 시 주의:

- `operation`이 catalog에 없으면 `UNSUPPORTED_OPERATION`을 반환합니다.
- 필수값이 없으면 네이버 API를 호출하지 않고 `VALIDATION_ERROR`를 반환합니다.
- 배송 방식에 따라 필수값이 달라지는 경우는 `conditionalRequired`로 검증합니다.
- path parameter는 `payload`에서 꺼내 endpoint에 삽입합니다.
- query parameter는 `payload`에서 허용된 key만 전달합니다.
- body parameter는 `payload`에서 허용된 key만 전달합니다.
- n8n이 직접 `endpoint`, `method`, `headers`를 보내서 네이버 API를 호출하게 하면 안 됩니다.

## 공식 문서

- [네이버 커머스 API LLM 문서 인덱스](https://apicenter.commerce.naver.com/llms/llms.txt)
- [RESTful API 공통 규칙](https://apicenter.commerce.naver.com/docs/restful-api)
