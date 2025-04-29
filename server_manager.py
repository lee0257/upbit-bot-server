from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

# 텔레그램 전송 함수 (연결 필요)
def send_telegram_alert(message):
    print(f"[텔레그램 알림] {message}")

# 가격 정보 저장소
price_history = {}

# 업비트 가격 조회 함수
def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        data = response.json()
        return data[0]['trade_price']
    except:
        return None

# 급등 포착 함수
def detect_price_surge():
    market = "KRW-BTC"
    while True:
        current_price = get_current_price(market)
        if current_price:
            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if rate >= 3:
                send_telegram_alert(f"[급등포착] {market}\n현재가: {current_price}원\n5분간 상승률: {rate:.2f}%")

        time.sleep(10)

# 급감 포착 함수
def detect_price_drop():
    market = "KRW-BTC"
    while True:
        current_price = get_current_price(market)
        if current_price:
            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 180]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if rate <= -5:
                send_telegram_alert(f"[급감포착] {market}\n현재가: {current_price}원\n3분간 하락률: {rate:.2f}%")

        time.sleep(10)

# 스윙매매 초입 포착 함수
def detect_swing_entry():
    market = "KRW-BTC"
    while True:
        current_price = get_current_price(market)
        if current_price:
            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if 0 < rate <= 2:
                send_telegram_alert(f"[스윙포착] {market}\n현재가: {current_price}원\n10분 내 상승률: {rate:.2f}%")

        time.sleep(10)

# 서버 실행
if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")

    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()

    app.run(host="0.0.0.0", port=8000)
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")
    app.run(host="0.0.0.0", port=8000)
