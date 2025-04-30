
from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

chat_ids = [
    "1901931119",  # 너
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
last_alert_time = {}

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        return response.json()[0]['trade_price']
    except:
        return None

def get_trade_volume(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        return response.json()[0]['acc_trade_price_24h'] / 144  # 약 10분 기준 거래대금 추정
    except:
        return 0

def get_korean_name_map():
    try:
        url = "https://api.upbit.com/v1/market/all"
        res = requests.get(url).json()
        return {item["market"]: item["korean_name"] for item in res}
    except:
        return {}

korean_name_map = get_korean_name_map()

def is_recently_alerted(market, cooldown=1800):
    now = time.time()
    if market in last_alert_time and now - last_alert_time[market] < cooldown:
        return True
    last_alert_time[market] = now
    return False

def detect_swing_entry():
    url = "https://api.upbit.com/v1/market/all"
    try:
        markets = requests.get(url).json()
    except:
        return

    for market_info in markets:
        market = market_info["market"]
        if not market.startswith("KRW-"):
            continue
        if market in ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]:
            continue

        def check_coin(market):
            while True:
                current_price = get_current_price(market)
                if current_price:
                    now = time.time()
                    price_history.setdefault(market, []).append((now, current_price))
                    price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

                    if len(price_history[market]) > 1:
                        _, oldest_price = price_history[market][0]
                        rate = ((current_price - oldest_price) / oldest_price) * 100
                        volume = get_trade_volume(market)

                        if rate >= 1.0 and volume >= 300000000 and not is_recently_alerted(market):
                            coin_name = korean_name_map.get(market, market)
                            msg = f"[추천코인1]\n" + \
                                  f"- 코인명: {market} ({coin_name})\n" + \
                                  f"- 현재가: {current_price}원\n" + \
                                  f"- 매수 추천가: {int(current_price * 0.985)} ~ {int(current_price * 1.005)}원\n" + \
                                  f"- 목표 매도가: {int(current_price * 1.05)}원\n" + \
                                  f"- 예상 수익률: 5%\n" + \
                                  f"- 예상 소요 시간: 1~3시간\n" + \
                                  f"- 추천 이유: 체결량 급증 + 매수 강세 포착\n" + \
                                  f"https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                            send_telegram_alert(msg)
                time.sleep(10)

        threading.Thread(target=check_coin, args=(market,), daemon=True).start()

if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
