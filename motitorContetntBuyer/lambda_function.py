import os
import requests
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import time

# ✅ 환경 변수에서 API 키와 웹훅 주소 불러오기
IMWEB_KEY = os.getenv("IMWEB_API_KEY")
IMWEB_SECRET = os.getenv("IMWEB_API_SECRET")
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL")

# ✅ DynamoDB 테이블 연결 (주문 기록용, 디스코드 회원 정보용)
dynamodb = boto3.resource("dynamodb")
order_table = dynamodb.Table("PROWOrderContentHistory")
discord_table = dynamodb.Table("PROWDiscordUser")

# ✅ IMWEB API에 로그인해서 access_token 받기
def get_access_token():
    try:
        url = "https://api.imweb.me/v2/auth"
        params = {"key": IMWEB_KEY, "secret": IMWEB_SECRET}
        response = requests.get(f"{url}?{urlencode(params)}")
        token = response.json()["access_token"]
        print("[SUCCESS][get_access_token] 토큰 발급 성공")
        return token
    except Exception as e:
        print(f"[ERROR][get_access_token] 토큰 발급 실패: {e}")
        raise

# ✅ UTC 시간을 한국 시간(KST)으로 변환하여 ISO 형식 문자열로 리턴
def format_kst(dt):
    kst = timezone(timedelta(hours=9))
    return dt.astimezone(kst).isoformat()

# ✅ 최근 2일 동안 '결제 완료된 주문'을 가져오는 함수
def fetch_orders(access_token):
    try:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=2)

        params = {
            "order_version": "v2",
            "type": "normal",
            "status": "PURCHASE_CONFIRMATION",
            "order_date_from": format_kst(start_time),
            "order_date_to": format_kst(now)
        }

        headers = {"Content-Type": "application/json", "access-token": access_token}
        response = requests.get("https://api.imweb.me/v2/shop/orders", params=params, headers=headers)
        data = response.json().get("data", {}).get("list", [])

        print(f"[SUCCESS][fetch_orders] 주문 수: {len(data)} | 범위: {params['order_date_from']} ~ {params['order_date_to']}")
        return data
    except Exception as e:
        print(f"[ERROR][fetch_orders] 주문 조회 실패: {e}")
        return []

# ✅ 주문번호를 이용하여 상세 주문 정보 가져오기
def fetch_order_detail(access_token, order_no):
    try:
        url = f"https://api.imweb.me/v2/shop/orders/{order_no}/prod-orders"
        headers = {"Content-Type": "application/json", "access-token": access_token}
        params = {"order_version": "v2"}
        response = requests.get(url, headers=headers, params=params)
        print(f"[SUCCESS][fetch_order_detail] 상세 조회 완료: {order_no}")
        return response.json()
    except Exception as e:
        print(f"[ERROR][fetch_order_detail] 주문 상세 조회 실패: {order_no} | {e}")
        return {}


# ✅ 해당 주문이 이미 처리됐는지 DynamoDB에서 확인
def is_order_processed(order_no):
    try:
        response = order_table.get_item(Key={"order_no": order_no})
        return "Item" in response
    except ClientError as e:
        print(f"[ERROR][is_order_processed] DynamoDB 조회 실패: {e.response['Error']['Message']}")
        return False


# ✅ 주문을 처리했음을 기록 (DynamoDB에 저장)
def mark_order_as_processed(order_info):
    try:
        order_table.put_item(Item=order_info)
        print(f"[SUCCESS][mark_order_as_processed] 주문 기록 완료: {order_info['order_no']}")
    except ClientError as e:
        print(f"[ERROR][mark_order_as_processed] 기록 실패: {e.response['Error']['Message']}")


# ✅ 전화번호로 디스코드 가입 여부와 userID 확인
def get_discord_info_by_phone(phone):
    try:
        response = discord_table.query(
            IndexName="phone-index",
            KeyConditionExpression=Key("phone").eq(phone)
        )
        items = response.get("Items", [])
        if items:
            print("[INFO][get_discord_info_by_phone] 가입자 발견")
            return items[0].get("userID", ""), "가입"
        else:
            print("[INFO][get_discord_info_by_phone] 미가입자")
            return "", "미가입"
    except Exception as e:
        print(f"[ERROR][get_discord_info_by_phone] Discord 유저 조회 실패: {e}")
        return "", "미가입"

# ✅ 웹훅 전송 (성공할 때까지 최대 3번 재시도)
def send_webhook(payload, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.post(ZAPIER_WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                print(f"[SUCCESS][send_webhook] 웹훅 전송 성공: order_no={payload.get('order_no')}")
                return True
            else:
                print(f"[ERROR][send_webhook] 실패 {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[ERROR][send_webhook] 예외 발생: {e}")

        if attempt < retries - 1:
            print(f"[RETRY][send_webhook] 재시도 {attempt + 1}/{retries}...")
            time.sleep(delay)

    print(f"[FATAL][send_webhook] 최종 실패: order_no={payload.get('order_no')}")
    return False

# ✅ Lambda 실행 시작점
def lambda_handler(event=None, context=None):
    print("[LOG][lambda_handler] 함수 시작")

    try:
        access_token = get_access_token()
        orders = fetch_orders(access_token)
        print(f"[INFO][lambda_handler] 전체 주문 수: {len(orders)}")

        # 배송 방식이 다운로드인 주문만 필터링
        download_orders = [o for o in orders if o.get("payment", {}).get("deliv_type") == "download"]
        print(f"[INFO][lambda_handler] 다운로드 주문 수: {len(download_orders)}")

        for order in download_orders:
            order_no = order.get("order_no")
            if not order_no:
                print("[SKIP][lambda_handler] order_no 없음")
                continue

            # 중복 처리 방지
            if is_order_processed(order_no):
                print(f"[SKIP][lambda_handler] 이미 처리된 주문: {order_no}")
                continue

            print(f"[PROCESS][lambda_handler] 주문 처리 시작: {order_no}")

            # 상세 상품 정보 가져오기
            detail = fetch_order_detail(access_token, order_no)
            
            # 🔍 [DEBUG] 전체 상세 정보 로그 (기존)
            # print(f"[DEBUGING]order info: {detail}") 
            
            items_group = detail.get("data", [])
            if not items_group:
                print(f"[WARNING][lambda_handler] 주문 상세 정보 없음: {order_no}")
                continue

            # 주문자 전화번호
            call = order.get("orderer", {}).get("call", "")
            user_id, discord_status = get_discord_info_by_phone(call)

            # 상품 목록 처리
            for group in items_group:
                for item in group.get("items", []):
                    prod_name = item.get("prod_name", "")
                    prod_custom_code = item.get("prod_custom_code", "")
                    
                    raw_options = item.get("options", [])
                    print(f"[INFO][lambda_handler] 옵션 그룹 수: {len(raw_options)}")

                    # 1) 옵션에서 기간 읽기(있으면 우선)
                    option_data = item.get("options", [[]])[0][0] if item.get("options") else {}
                    raw_values = option_data.get("value_name_list", [])
                    value_name_list = [v.split("(")[0].strip() for v in raw_values if isinstance(v, str)]
                    기간 = value_name_list[0] if value_name_list else ""
                    
                    # 2) ✅ 정기구독(매월 결제) 커스텀코드면 무조건 1개월
                    if prod_custom_code == "BEPL-MEMBERSHIP-365":
                        기간 = "1개월"
                        
                    # 3) 옵션이 없는 일반 컨텐츠는 기존 기본값 유지(12개월/36개월)
                    if not 기간:
                        기간 = "36개월" if "우아한 영어" in prod_name else "12개월"

                    # ✅ 구독 여부/타입/주기 (Zapier용 최소 정보)
                    is_subscription = "구독" if prod_custom_code == "BEPL-MEMBERSHIP-365" else "'"


                    # 웹훅 전송용 데이터 구성
                    payload = {
                        "order_no": [order_no],
                        "prod_name": [prod_name],
                        "call": [call],
                        "value_name_list": [기간],
                        "userID": [user_id],
                        "디스코드 가입 여부": [discord_status],
                        "is_subscription": [is_subscription],
                    }

                    print(f"[INFO][lambda_handler] 웹훅 전송 준비 - 주문: {order_no}, 상품: {prod_name}")
                    send_webhook(payload)

            # DynamoDB에 주문 처리 완료 기록
            order_info = {
                "order_no": order_no,
                "phone": call,
                "program": items_group[0].get("items", [{}])[0].get("prod_name", ""),
                "period": 기간
            }
            mark_order_as_processed(order_info)

        return {
            "statusCode": 200,
            "body": f"{len(download_orders)}건 처리 완료"
        }

    except Exception as e:
        print(f"[FATAL][lambda_handler] 전체 오류 발생: {str(e)}")
        # 에러 로그도 더 상세하게 보기 위해 traceback 추가 가능하지만, 일단 요청하신대로 간단히 유지
        return {
            "statusCode": 500,
            "body": "에러 발생"
        }
