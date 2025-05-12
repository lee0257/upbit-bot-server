from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

chat_ids = ["1901931119"]  # 테스트용 사용자 ID만 사용
token = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"

def send_telegram(message):
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            print("텔레그램 전송 실패")

price_data = {}

def get_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        res = requests.get(url)
        return res.json()[0]["trade_price"]
    except:
        return None

def detect_surge():
    markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SUI", "KRW-NEAR"]
    while True:
        now = time.time()
        for market in markets:
            price = get_price(market)
            if price:
                price_data.setdefault(market, []).append((now, price))
                price_data[market] = [(t, p) for t, p in price_data[market] if now - t <= 600]

                old_time, old_price = price_data[market][0]
                rate = (price - old_price) / old_price * 100

                if 1.5 <= rate <= 2.5:  # 선행 포착 범위
                    send_telegram(
                        f"[선행급등포착] {market}\n"
                        f"현재가: {price}원\n"
                        f"10분 전 대비 상승률: {rate:.2f}%"
                    )
        time.sleep(15)

@app.route("/")
def home():
    return "선행포착 테스트 서버 실행 중"

if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_surge, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
