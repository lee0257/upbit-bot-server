from flask import Flask
import threading
import time
import requests
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "업비트 자동 봇 서버 실행 중!"

# 알림 보낼 사용자들
chat_ids = ["1901931119", "7146684315"]
token = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"

def send_telegram_alert(message):
    for chat_id in chat_ids:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": message}
            )
        except:
            print(f"[전송 실패] {chat_id}")

# 중복 방지 및 데이터 저장
price_history = {}
last_alert_time = {}

# 필터 조건
MIN_VOLUME = 1200000000  # 거래대금 최소 12억
MIN_RATE = 2.0           # 상승률 2%
DUPLICATE_MINUTES = 30   # 30분 이내 중복방지

# 한글명 불러오기 (초기 1회)
def fetch_market_info():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all?isDetails=true")
        data = response.json()
        return {
            item["market"]: item["korean_name"]
            for item in data
            if item["market"].startswith("KRW-")
        }
    except:
        return {}

market_name_map = fetch_market_info()

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        return response.json()[0]
    except:
        return None

def detect_surge():
    while True:
        for market in market_name_map.keys():
            now = time.time()

            # 가격 및 거래대금 정보
            data = get_current_price(market)
            if not data:
                continue

            price = data["trade_price"]
            acc_volume = data["acc_trade_price_24h"]

            # 거래대금 필터링
            if acc_volume < MIN_VOLUME:
                continue

            # 가격 저장 및 기간 내 비교
            price_history.setdefault(market, []).append((now, price))
            price_history[market] = [
                (t, p) for t, p in price_history[market] if now - t <= 600
            ]

            if len(price_history[market]) < 2:
                continue

            base_time, base_price = price_history[market][0]
            rate = ((price - base_price) / base_price) * 100

            if rate >= MIN_RATE:
                # 중복 방지
                last_time = last_alert_time.get(market)
                if last_time and now - last_time < DUPLICATE_MINUTES * 60:
                    continue
                last_alert_time[market] = now

                message = (
                    f"[스윙포착 🌊]\n"
                    f"- 코인명: {market_name_map[market]} ({market})\n"
                    f"- 현재가: {int(price)}원\n"
                    f"- 상승률: {rate:.2f}% (10분)\n"
                    f"- 조건: 거래대금 12억↑ + 선행포착\n"
                    f"- 링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
                send_telegram_alert(message)

        time.sleep(10)

# 실행
if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_surge, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
