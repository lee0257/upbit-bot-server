from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

# 텔레그램 ID
chat_ids = ["1901931119", "7146684315"]

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
last_alert_time = {}  # 각 market별 마지막 알림 시간

def get_all_markets():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all?isDetails=false")
        data = response.json()
        return [item['market'] for item in data if item['market'].startswith("KRW-")]
    except:
        return ["KRW-BTC"]  # 실패 시 기본값

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        data = response.json()
        return data[0]['trade_price']
    except:
        return None

def detect_price_surge():
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history.setdefault(market, []).append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]
                if len(price_history[market]) > 0:
                    oldest_time, oldest_price = price_history[market][0]
                    rate = ((current_price - oldest_price) / oldest_price) * 100
                    last_time = last_alert_time.get(f"{market}_surge", 0)
                    if rate >= 5 and now - last_time >= 1800:  # 30분 중복 방지
                        send_telegram_alert(f"[급등포착 🔥]\n코인명: {market}\n현재가: {current_price}원\n5분 상승률: {rate:.2f}%\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}")
                        last_alert_time[f"{market}_surge"] = now
        time.sleep(10)

def detect_price_drop():
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history.setdefault(market, []).append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]
                if len(price_history[market]) > 0:
                    oldest_time, oldest_price = price_history[market][0]
                    rate = ((current_price - oldest_price) / oldest_price) * 100
                    last_time = last_alert_time.get(f"{market}_drop", 0)
                    if rate <= -5 and now - last_time >= 1800:  # 30분 중복 방지
                        send_telegram_alert(f"[급락포착 💧]\n코인명: {market}\n현재가: {current_price}원\n5분 하락률: {rate:.2f}%\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}")
                        last_alert_time[f"{market}_drop"] = now
        time.sleep(10)

def detect_swing_entry():
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history.setdefault(market, []).append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]
                if len(price_history[market]) > 0:
                    oldest_time, oldest_price = price_history[market][0]
                    rate = ((current_price - oldest_price) / oldest_price) * 100
                    last_time = last_alert_time.get(f"{market}_swing", 0)
                    if 0 < rate <= 2 and now - last_time >= 1800:  # 30분 중복 방지
                        send_telegram_alert(f"[스윙포착 🌊]\n코인명: {market}\n현재가: {current_price}원\n10분 상승률: {rate:.2f}%\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}")
                        last_alert_time[f"{market}_swing"] = now
        time.sleep(10)

if __name__ == "__main__":
    print("서버 매니저 실행 중...")

    markets = get_all_markets()  # 업비트 전체 KRW마켓 가져오기
    print(f"모니터링 코인: {markets}")

    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()

    app.run(host="0.0.0.0", port=8000)
