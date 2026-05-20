# GenerateClientSecretSign

네이버 커머스 API 호출에 필요한 `access_token`을 발급하는 내부 인증 Lambda입니다.

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 런타임 | Node.js |
| 진입점 | `index.handler` |
| 주요 의존성 | `axios`, `bcryptjs` |
| 트리거 | API Gateway 또는 내부 Lambda 호출 |
| 외부 API | `https://api.commerce.naver.com/external/v1/oauth2/token` |

## 역할

이 Lambda는 네이버 커머스 API의 OAuth 토큰 발급 절차를 캡슐화합니다.

`naver-commerce-api` Lambda가 이 함수를 호출해 `access_token`을 받은 뒤, 해당 토큰으로 실제 네이버 커머스 API를 호출합니다.

## 요청 형식

`POST` 요청 body는 JSON이어야 합니다.

```json
{
  "client_id": "NAVER_CLIENT_ID",
  "client_secret": "NAVER_CLIENT_SECRET",
  "type": "SELF"
}
```

| 필드 | 필수 | 설명 |
| --- | :---: | --- |
| `client_id` | 필수 | 네이버 커머스 API client ID |
| `client_secret` | 필수 | 네이버 커머스 API client secret. 앞뒤 공백은 제거됩니다. |
| `type` | 필수 | 보통 `SELF` |

현재 구현은 `client_id`, `client_secret`, `type`만 네이버 토큰 API로 전달합니다.

## 처리 흐름

1. `event.body`를 JSON으로 파싱합니다.
2. `client_id`, `client_secret`, `type` 필수값을 검증합니다.
3. `Date.now()`로 millisecond timestamp를 생성합니다.
4. `{client_id}_{timestamp}` 형식의 password를 만듭니다.
5. `client_secret`을 bcrypt salt로 사용해 password를 해싱합니다.
6. bcrypt 결과를 Base64로 인코딩해 `client_secret_sign`을 만듭니다.
7. 네이버 토큰 API를 `POST`로 호출합니다.
8. 네이버 응답을 호출자에게 반환합니다.

네이버 토큰 API 요청값은 body가 아니라 query parameter로 전송합니다. `client_secret_sign`에 `+`, `/`, `=` 같은 문자가 포함될 수 있어 `axios`의 `params` 인코딩을 사용합니다.

## 성공 응답

성공하면 네이버 OAuth token API 응답을 그대로 반환합니다.

```json
{
  "access_token": "...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

Lambda 응답 구조:

```json
{
  "statusCode": 200,
  "body": "{...네이버 응답 JSON 문자열...}"
}
```

## 실패 응답

네이버 API가 실패하면 네이버 HTTP status를 최대한 유지합니다.

```json
{
  "result": "API 요청 오류 발생",
  "status": 400,
  "data": {
    "code": "...",
    "message": "..."
  }
}
```

요청 파싱 실패, 필수값 누락, 해싱 오류 같은 내부 오류는 현재 `500`으로 반환합니다.

```json
{
  "result": "서버 내부 오류",
  "error": "client_id가 전달되지 않았습니다."
}
```

## 환경변수

이 Lambda는 별도 환경변수를 사용하지 않습니다. 인증에 필요한 값은 내부 호출자가 요청 body로 전달합니다.

## 배포 패키지

```bash
npm ci --omit=dev
zip -r GenerateClientSecretSign.zip index.js package.json package-lock.json node_modules
```

GitHub에는 `node_modules/`를 커밋하지 않습니다.

## 로그와 보안

- `client_secret`, bcrypt hash, `client_secret_sign`, `access_token`은 로그에 남기지 않습니다.
- 요청 body 전체를 로그에 남기지 않습니다.
- 이 Lambda는 외부 브라우저 사용자가 직접 호출하는 용도가 아닙니다.
- API Gateway 또는 Lambda invoke 권한은 `naver-commerce-api` 등 내부 호출자에게만 허용합니다.

## 변경 이력

| 날짜 | 변경 내용 |
| --- | --- |
| 2025-04-14 | access token 발급용 Lambda 구조 정비 |
| 2026-01-05 | 네이버 커머스 API 최신 인증 방식 반영 |
| 2026-05-20 | README.md 형식 통일, 실제 응답/보안 정책 반영 |

