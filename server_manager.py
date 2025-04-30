from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Upbit Auto Alert Server Running"

chat_ids = ["1901931119", "7146684315"]
token = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
alert_history = {}

def send_alert(message):
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": message})
        except:
            print(f"[ERROR] Failed to send to {chat_id}")

def get_current_price(market):
    try:
        response = requests.get(f"https://api.upbit.com/v1/ticker?markets={market}")
        return response.json()[0]['trade_price']
    except:
        return None

def get_market_name_map():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all?isDetails=true")
        market_data = response.json()
        return {item['market']: item['korean_name'] for item in market_data}
    except:
        return {}

market_names = get_market_name_map()
price_data = {}

def should_alert(market, alert_type):
    now = time.time()
    key = f"{market}_{alert_type}"
    if key in alert_history and now - alert_history[key] < 1800:
        return False
    alert_history[key] = now
    return True

def detect_swing():
    while True:
        markets = [m for m in market_names if m.startswith("KRW-") and not m.startswith(("KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-SOL"))]
        for market in markets:
            try:
                candles = requests.get(f"https://api.upbit.com/v1/candles/minutes/1?market={market}&count=11").json()
                if len(candles) < 10:
                    continue

                now_price = candles[0]['trade_price']
                past_price = candles[10]['trade_price']
                rate = ((now_price - past_price) / past_price) * 100
                volume = candles[0]['candle_acc_trade_price']

                if rate >= 1.0 and volume >= 120000000:
                    if not should_alert(market, "swing"):
                        continue

                    name = market_names.get(market, market)
                    msg = f"[스윙포착 🌊]\n- 코인명: {name}\n- 현재가: {now_price}원\n- 매수 추천가: {int(now_price*0.99)} ~ {int(now_price*1.01)}원\n- 목표 매도가: {int(now_price*1.05)}원\n- 예상 수익률: 5%\n- 예상 소요 시간: 1~3시간\n- 추천 이유: 상승 초입 진입 구간 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    send_alert(msg)

            except:
                continue
        time.sleep(15)

def detect_surge():
    while True:
        markets = [m for m in market_names if m.startswith("KRW-")]
        for market in markets:
            try:
                candles = requests.get(f"https://api.upbit.com/v1/candles/minutes/1?market={market}&count=6").json()
                if len(candles) < 5:
                    continue

                now_price = candles[0]['trade_price']
                past_price = candles[5]['trade_price']
                rate = ((now_price - past_price) / past_price) * 100
                volume = candles[0]['candle_acc_trade_price']

                if rate >= 3.0 and volume >= 100000000:
                    if not should_alert(market, "surge"):
                        continue

                    name = market_names.get(market, market)
                    msg = f"[급등포착 🔥]\n- 코인명: {name}\n- 현재가: {now_price}원\n- 매수 추천가: {int(now_price*0.99)} ~ {int(now_price*1.01)}원\n- 목표 매도가: {int(now_price*1.05)}원\n- 예상 수익률: 5%\n- 예상 소요 시간: 10~30분\n- 추천 이유: 체결량 급증 + 매수 강세 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    send_alert(msg)

            except:
                continue
        time.sleep(15)

def detect_drop():
    while True:
        markets = [m for m in market_names if m.startswith("KRW-")]
        for market in markets:
            try:
                candles = requests.get(f"https://api.upbit.com/v1/candles/minutes/1?market={market}&count=4").json()
                if len(candles) < 3:
                    continue

                now_price = candles[0]['trade_price']
                past_price = candles[3]['trade_price']
                rate = ((now_price - past_price) / past_price) * 100

                if rate <= -5.0:
                    if not should_alert(market, "drop"):
                        continue

                    name = market_names.get(market, market)
                    msg = f"[급락포착 💧]\n- 코인명: {name}\n- 현재가: {now_price}원\n- 매수 추천가: {int(now_price*0.99)} ~ {int(now_price*1.01)}원\n- 목표 매도가: {int(now_price*1.05)}원\n- 예상 수익률: 5%\n- 예상 소요 시간: 1~2시간\n- 추천 이유: 단기 급락 후 반등 구간 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    send_alert(msg)

            except:
                continue
        time.sleep(15)

if __name__ == "__main__":
    print("서버 실행 시작")
    threading.Thread(target=detect_swing, daemon=True).start()
    threading.Thread(target=detect_surge, daemon=True).start()
    threading.Thread(target=detect_drop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
