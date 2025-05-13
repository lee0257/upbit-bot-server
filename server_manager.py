import asyncio
import json
import websockets
import requests
import time
from datetime import datetime

# ===== 사용자 설정 =====
TELEGRAM_TOKEN = "6437254217:AAF-oFmu6cRrBqEUZ5xwDb2cm7I0XAfdb9w"
TELEGRAM_CHAT_ID = "1901931119"
ALERT_INTERVAL = 1800  # 중복 알림 차단 시간 (초) = 30분

# ===== 내부 상태 저장 =====
last_alert_time = {}
KRW_MARKET = []

# ===== 텔레그램 전송 함수 =====
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# ===== 마켓 한글명 불러오기 =====
def fetch_market_info():
    global KRW_MARKET
    url = "https://api.upbit.com/v1/market/all"
    res = requests.get(url).json()
    KRW_MARKET = [m for m in res if m['market'].startswith('KRW-') and not m['market_warning'] == 'CAUTION']

# ===== 급등 조건 체크 함수 =====
def is_surge_condition(data):
    try:
        market = data['code']
        now_price = float(data['trade_price'])
        acc_volume = float(data['acc_trade_price_24h'])
        ask_bid = data['ask_bid']

        # 필터: 거래대금 5억 이상
        if acc_volume < 500000000:
            return False

        # 중복 알림 차단
        now = time.time()
        if market in last_alert_time and now - last_alert_time[market] < ALERT_INTERVAL:
            return False

        # 체결 방향 + 매수 강도 필터
        if ask_bid == "BID":  # 매수 체결
            last_alert_time[market] = now
            return True

        return False

    except Exception as e:
        print("조건 체크 오류:", e)
        return False

# ===== 급등 메시지 구성 =====
def format_message(data):
    market = data['code']
    price = int(data['trade_price'])
    name = next((m['korean_name'] for m in KRW_MARKET if m['market'] == market), market)
    msg = f"[선행급등포착]\n- 코인명: {name}\n- 현재가: {price}원\n- 추천 이유: 매수세 유입 + 거래대금 기준 초과"
    return msg

# ===== 업비트 WebSocket 수신 =====
async def run():
    fetch_market_info()
    codes = [m['market'] for m in KRW_MARKET]
    url = "wss://api.upbit.com/websocket/v1"
    while True:
        try:
            async with websockets.connect(url) as ws:
                subscribe = [{"ticket":"test"}, {"type":"trade","codes":codes}]
                await ws.send(json.dumps(subscribe))
                while True:
                    data = await ws.recv()
                    parsed = json.loads(data)
                    if is_surge_condition(parsed):
                        message = format_message(parsed)
                        send_telegram_message(message)
        except Exception as e:
            print("WebSocket 오류 발생, 재연결 중...", e)
            await asyncio.sleep(3)

if __name__ == '__main__':
    asyncio.run(run())
