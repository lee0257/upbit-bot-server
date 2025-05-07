from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

# 알림 대상
chat_ids = ["1901931119", "7146684315"]

token = "YOUR_TELEGRAM_BOT_TOKEN"  # ← 실제 토큰 넣어줘

# 알림 함수
def send_telegram_alert(message):
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            print(f"[텔레그램 전송 실패] 대상: {chat_id}")

price_history = {}
last_alert_time = {}

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        data = response.json()
        return data[0]['trade_price'], data[0]['acc_trade_price_24h']
    except:
        return None, None

def is_recent_alert(market):
    now = time.time()
    if market in last_alert_time and now - last_alert_time[market] < 1800:  # 30분 중복 방지
        return True
    last_alert_time[market] = now
    return False

def detect_price_surge():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA"]  # 테스트용
    while True:
        for market in markets:
            current_price, trade_vol = get_current_price(market)
            if not current_price or trade_vol < 1500000000:  # 거래대금 1,500백만 미만 제외
                continue

            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if rate >= 2 and not is_recent_alert(market):
                message = (
                    f"[급등포착 🔥]\n"
                    f"- 코인명: {market}\n"
                    f"- 현재가: {current_price:.0f}원\n"
                    f"- 상승률(10분): {rate:.2f}%\n"
                    f"- 거래대금: {trade_vol/1000000:.1f}백만\n"
                    f"- https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
                send_telegram_alert(message)
        time.sleep(10)

def detect_price_drop():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA"]
    while True:
        for market in markets:
            current_price, trade_vol = get_current_price(market)
            if not current_price or trade_vol < 1500000000:
                continue

            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if rate <= -5 and not is_recent_alert(market):
                message = (
                    f"[급락포착 💧]\n"
                    f"- 코인명: {market}\n"
                    f"- 현재가: {current_price:.0f}원\n"
                    f"- 하락률(5분): {rate:.2f}%\n"
                    f"- 거래대금: {trade_vol/1000000:.1f}백만\n"
                    f"- https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
                send_telegram_alert(message)
        time.sleep(10)

def detect_swing_entry():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA"]
    while True:
        for market in markets:
            current_price, trade_vol = get_current_price(market)
            if not current_price or trade_vol < 1500000000:
                continue

            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if 0.8 < rate <= 2 and not is_recent_alert(market):
                message = (
                    f"[스윙포착 🌊]\n"
                    f"- 코인명: {market}\n"
                    f"- 현재가: {current_price:.0f}원\n"
                    f"- 상승률(10분): {rate:.2f}%\n"
                    f"- 거래대금: {trade_vol/1000000:.1f}백만\n"
                    f"- https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
                send_telegram_alert(message)
        time.sleep(10)

if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
