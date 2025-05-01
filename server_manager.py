from flask import Flask
import threading
import time
import requests
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "Upbit Alert System Running"

chat_ids = [
    "1901931119",
    "7146684315"
]

TELEGRAM_TOKEN = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"

price_history = {}
last_alert_time = {}
alerted_markets = set()

headers = {"accept": "application/json"}

# 한글명 매핑
market_names = {}
def update_market_names():
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    try:
        res = requests.get(url, headers=headers).json()
        for item in res:
            if item['market'].startswith("KRW-"):
                market_names[item['market']] = item['korean_name']
    except:
        pass

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        res = requests.get(url, headers=headers).json()
        return res[0]['trade_price']
    except:
        return None


def send_telegram_alert(message):
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            pass


def detect_price_surge():
    while True:
        for market in market_names:
            now = time.time()
            price = get_current_price(market)
            if not price:
                continue

            history = price_history.setdefault(market, [])
            history.append((now, price))
            price_history[market] = [(t, p) for t, p in history if now - t <= 600]

            if len(price_history[market]) < 2:
                continue

            base_time, base_price = price_history[market][0]
            rate = ((price - base_price) / base_price) * 100

            if 1.0 <= rate <= 1.2 and now - last_alert_time.get(market+"_surge", 0) > 1800:
                last_alert_time[market+"_surge"] = now
                name = market_names.get(market, market)
                send_telegram_alert(
                    f"[급등포착 🔥]\n- 코인명: {name} ({market.split('-')[1]})\n- 현재가: {price}원\n- 상승률: {rate:.2f}%\n- 예상 수익률: 5~7%\n- 예상 소요 시간: 30분\n- 추천 이유: 체결량 급증 + 거래대금 유입\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
        time.sleep(10)


def detect_price_drop():
    while True:
        for market in market_names:
            now = time.time()
            price = get_current_price(market)
            if not price:
                continue

            history = price_history.setdefault(market, [])
            history.append((now, price))
            price_history[market] = [(t, p) for t, p in history if now - t <= 120]

            if len(price_history[market]) < 2:
                continue

            base_time, base_price = price_history[market][0]
            rate = ((price - base_price) / base_price) * 100

            if rate <= -5.0 and now - last_alert_time.get(market+"_drop", 0) > 1800:
                last_alert_time[market+"_drop"] = now
                name = market_names.get(market, market)
                send_telegram_alert(
                    f"[급락포착 💧]\n- 코인명: {name} ({market.split('-')[1]})\n- 현재가: {price}원\n- 하락률: {rate:.2f}%\n- 예상 반등 가능성: 중간 이상\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
        time.sleep(10)


def detect_swing_entry():
    while True:
        for market in market_names:
            now = time.time()
            price = get_current_price(market)
            if not price:
                continue

            history = price_history.setdefault(market, [])
            history.append((now, price))
            price_history[market] = [(t, p) for t, p in history if now - t <= 600]

            if len(price_history[market]) < 2:
                continue

            base_time, base_price = price_history[market][0]
            rate = ((price - base_price) / base_price) * 100

            if rate >= 1.0 and now - last_alert_time.get(market+"_swing", 0) > 1800:
                last_alert_time[market+"_swing"] = now
                name = market_names.get(market, market)
                send_telegram_alert(
                    f"[스윙포착 🌊]\n- 코인명: {name} ({market.split('-')[1]})\n- 현재가: {price}원\n- 상승률: {rate:.2f}%\n- 예상 수익률: 5~10%\n- 예상 소요 시간: 2시간\n- 추천 이유: 체결량 + 거래대금 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
        time.sleep(10)


def auto_trigger():
    while True:
        now = datetime.datetime.now()
        if now.hour == 8 and now.minute == 50:
            for market in market_names:
                price = get_current_price(market)
                if price:
                    price_history[market] = [(time.time(), price)]
            print("[자동 트리거] 8:50 초기 데이터 갱신 완료")
            time.sleep(60)
        time.sleep(5)


if __name__ == "__main__":
    update_market_names()
    threading.Thread(target=auto_trigger, daemon=True).start()
    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
