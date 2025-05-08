from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

chat_ids = [
    "1901931119",  # 너의 ID
    "7146684315"   # 친구 ID 추가
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

markets = [
    "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOGE",
    "KRW-SOL", "KRW-AVAX", "KRW-DOT", "KRW-LTC", "KRW-BCH",
    "KRW-TRX", "KRW-ETC", "KRW-XLM", "KRW-MATIC", "KRW-NEAR",
    "KRW-APT", "KRW-SUI", "KRW-ARB", "KRW-ICP", "KRW-IMX",
    "KRW-FTM", "KRW-AAVE", "KRW-OP", "KRW-PEPE", "KRW-STX",
    "KRW-HBAR", "KRW-ALGO", "KRW-CHZ", "KRW-GALA", "KRW-SAND",
    "KRW-HIFI", "KRW-AXS", "KRW-MANA", "KRW-1INCH", "KRW-ENS",
    "KRW-ZIL", "KRW-BAT", "KRW-IOST", "KRW-CVC", "KRW-POLYX",
    "KRW-SSV", "KRW-YGG", "KRW-WAVES", "KRW-PLA", "KRW-MASK",
    "KRW-RSR", "KRW-TON", "KRW-CELO", "KRW-XEM", "KRW-QTUM",
    "KRW-STEEM", "KRW-ONT", "KRW-ICX", "KRW-ANKR", "KRW-MLK",
    "KRW-GLM", "KRW-KAVA", "KRW-NU", "KRW-STPT", "KRW-API3"
]

price_history = {}
last_alert_time = {}

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
                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100
                last_time = last_alert_time.get(market, 0)
                if rate >= 5 and now - last_time >= 1800:  # 5% 상승, 30분 중복 방지
                    send_telegram_alert(f"[급등포착 🔥]\n코인명: {market}\n현재가: {current_price}원\n5분 상승률: {rate:.2f}%\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}")
                    last_alert_time[market] = now
        time.sleep(10)

def detect_price_drop():
    while True:
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history.setdefault(market, []).append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 300]
                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100
                last_time = last_alert_time.get(f"{market}_drop", 0)
                if rate <= -5 and now - last_time >= 1800:  # 5% 하락, 30분 중복 방지
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
                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100
                last_time = last_alert_time.get(f"{market}_swing", 0)
                if 2 <= rate <= 5 and now - last_time >= 1800:  # 2~5% 상승, 30분 중복 방지
                    send_telegram_alert(f"[스윙포착 🌊]\n코인명: {market}\n현재가: {current_price}원\n10분 상승률: {rate:.2f}%\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}")
                    last_alert_time[f"{market}_swing"] = now
        time.sleep(10)

if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
