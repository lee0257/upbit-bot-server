from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

# 여러 사용자에게 알림 전송
chat_ids = [
    "1901931119",  # 너의 ID
    "7146684315"   # 친구 ID
]

def send_telegram_alert(message):
    token = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            print(f"[텔레그램 전송 실패] 대상: {chat_id}")

price_history = {}

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        data = response.json()
        return data[0]['trade_price']
    except:
        return None

def detect_price_surge():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]  # 예시, 필요한 코인 추가
    for market in markets:
        price_history.setdefault(market, [])
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history[market].append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]
                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100
                if rate >= 3:
                    send_telegram_alert(
                        f"[급등포착 🔥]\n코인명: {market}\n현재가: {current_price}원\n"
                        f"5분간 상승률: {rate:.2f}%\n"
                        f"링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )
        time.sleep(10)

def detect_price_drop():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
    for market in markets:
        price_history.setdefault(market, [])
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history[market].append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]
                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100
                if rate <= -5:
                    send_telegram_alert(
                        f"[급락포착 💧]\n코인명: {market}\n현재가: {current_price}원\n"
                        f"5분간 하락률: {rate:.2f}%\n"
                        f"링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )
        time.sleep(10)

def detect_swing_entry():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
    for market in markets:
        price_history.setdefault(market, [])
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history[market].append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]
                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100
                if 0 < rate <= 2:
                    send_telegram_alert(
                        f"[스윙포착 🌊]\n코인명: {market}\n현재가: {current_price}원\n"
                        f"10분 내 상승률: {rate:.2f}%\n"
                        f"링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )
        time.sleep(10)

if __name__ == "__main__":
    print("서버 매니저 실행되었습니다.")
    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
