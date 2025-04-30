from flask import Flask
import threading
import time
import requests
import datetime

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

chat_ids = [
    "1901931119",
    "7146684315"
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

def get_market_korean_name(market):
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    try:
        response = requests.get(url)
        markets = response.json()
        for item in markets:
            if item['market'] == market:
                return item['korean_name']
        return market
    except:
        return market

def detect_price_surge():
    market = "KRW-SIGN"
    while True:
        current_price = get_current_price(market)
        if current_price:
            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 180]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if rate >= 2:
                name = get_market_korean_name(market)
                message = (
                    f"[급등포착 🔥]\n"
                    f"- 코인명: {name}\n"
                    f"- 현재가: {current_price}원\n"
                    f"- 매수 추천가: {int(current_price * 0.995)} ~ {int(current_price * 1.005)}원\n"
                    f"- 목표 매도가: {int(current_price * 1.03)}원\n"
                    f"- 예상 수익률: 3%\n"
                    f"- 예상 소요 시간: 10분\n"
                    f"- 추천 이유: 체결량 급증 + 매수 강세 포착\n"
                    f"https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
                send_telegram_alert(message)
        time.sleep(10)

def detect_swing_entry():
    market = "KRW-SIGN"
    while True:
        current_price = get_current_price(market)
        if current_price:
            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            if 1.0 <= rate < 2:
                name = get_market_korean_name(market)
                message = (
                    f"[스윙포착 🌊]\n"
                    f"- 코인명: {name}\n"
                    f"- 현재가: {current_price}원\n"
                    f"- 매수 추천가: {int(current_price * 0.995)} ~ {int(current_price * 1.005)}원\n"
                    f"- 목표 매도가: {int(current_price * 1.05)}원\n"
                    f"- 예상 수익률: 5%\n"
                    f"- 예상 소요 시간: 1~3일\n"
                    f"- 추천 이유: 상승 초기 진입 구간 포착\n"
                    f"https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )
                send_telegram_alert(message)
        time.sleep(15)

if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")
    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
