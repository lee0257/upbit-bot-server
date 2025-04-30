from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

# 알림 대상 채팅 ID 목록
chat_ids = [
    "1901931119",  # 유저 본인
    "7146684315"   # 친구
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

def detect_swing_entry():
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    try:
        markets = requests.get(url).json()
    except:
        return

    for market_info in markets:
        market = market_info["market"]
        if not market.startswith("KRW-"):
            continue
        if market in ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]:
            continue  # 시총 상위 제외

        def check_coin(market):
            while True:
                current_price = get_current_price(market)
                if current_price:
                    now = time.time()
                    price_history.setdefault(market, []).append((now, current_price))
                    price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]
                    if len(price_history[market]) > 1:
                        oldest_time, oldest_price = price_history[market][0]
                        rate = ((current_price - oldest_price) / oldest_price) * 100
                        if rate >= 1:
                            send_telegram_alert(
                                f"[스윙포착 🌊] {market}\n현재가: {current_price}원\n10분 내 상승률: {rate:.2f}%\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                            )
                time.sleep(10)
        threading.Thread(target=check_coin, args=(market,), daemon=True).start()

if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
