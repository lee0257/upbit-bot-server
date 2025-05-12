from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

# 텔레그램 설정
TOKEN = "여기에_봇_토큰_입력"
CHAT_IDS = ["1901931119", "7146684315"]  # 사용자 ID들

# 중복 알림 방지용
last_alert_times = {}
alert_interval = 1800  # 30분 (초)

# 상장폐지 예정 코인 제외 리스트 (예시)
delisting_list = ["KRW-BTT", "KRW-MOC", "KRW-BOUNTY"]  # 필요시 추가

# 선행포착 감지를 위한 가격 기록
price_history = {}

def send_alert(message):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": message}
            requests.post(url, data=data)
        except:
            print(f"[전송 실패] {chat_id}")

def get_current_price_and_volume(market):
    try:
        response = requests.get(f"https://api.upbit.com/v1/ticker?markets={market}")
        data = response.json()[0]
        return data["trade_price"], data["acc_trade_price_24h"]
    except:
        return None, None

def get_market_list():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all?isDetails=false")
        data = response.json()
        return [item["market"] for item in data if item["market"].startswith("KRW-") and item["market"] not in delisting_list]
    except:
        return []

def get_korean_name(market):
    try:
        response = requests.get("https://api.upbit.com/v1/market/all")
        data = response.json()
        for item in data:
            if item["market"] == market:
                return item["korean_name"]
        return market
    except:
        return market

def detect_surge_candidates():
    markets = get_market_list()
    now = time.time()

    for market in markets:
        price, volume = get_current_price_and_volume(market)
        if price is None or volume is None or volume < 1200000000:
            continue

        price_history.setdefault(market, []).append((now, price))
        price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

        if len(price_history[market]) < 2:
            continue

        oldest_time, oldest_price = price_history[market][0]
        rate = ((price - oldest_price) / oldest_price) * 100

        # 알림 조건: 10분 내 2% 이상 상승 + 거래대금 조건 + 중복 차단
        if rate >= 2.0:
            if market in last_alert_times and now - last_alert_times[market] < alert_interval:
                continue

            last_alert_times[market] = now
            name = get_korean_name(market)
            msg = (
                f"[스윙포착 🌊]\n"
                f"- 코인명: {name} ({market})\n"
                f"- 현재가: {price}원\n"
                f"- 상승률: {rate:.2f}% (10분)\n"
                f"- 조건: 거래대금 12억↑ + 선행포착\n"
                f"- 링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
            )
            send_alert(msg)

def start_monitoring():
    while True:
        try:
            detect_surge_candidates()
        except Exception as e:
            print(f"[오류] {e}")
        time.sleep(10)

@app.route("/")
def index():
    return "업비트 자동 알림 서버 실행 중!"

if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=start_monitoring, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
