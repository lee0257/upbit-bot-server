from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Upbit Alert System Running"

# 텔레그램 알림 설정
chat_ids = [
    "1901931119",  # 사용자 본인
    "7146684315"   # 친구 추가
]
TELEGRAM_TOKEN = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"

# 실시간 가격 조회
price_history = {}

def get_current_price(market):
    try:
        url = f"https://api.upbit.com/v1/ticker?markets={market}"
        response = requests.get(url)
        return response.json()[0]['trade_price']
    except:
        return None

def send_telegram_alert(message):
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            print(f"[전송 실패] 대상: {chat_id}")

# 급등포착
last_alert_time = {}
def detect_price_surge():
    market = "KRW-BTC"
    while True:
        price = get_current_price(market)
        if not price:
            time.sleep(10)
            continue

        now = time.time()
        history = price_history.setdefault(market, [])
        history.append((now, price))
        price_history[market] = [(t, p) for t, p in history if now - t <= 600]

        base_time, base_price = price_history[market][0]
        rate = ((price - base_price) / base_price) * 100

        # 급등 조건 (선행포착)
        if 1.0 <= rate <= 1.2 and now - last_alert_time.get(market, 0) > 1800:
            last_alert_time[market] = now
            send_telegram_alert(
                f"[급등포착 🔥]\n- 코인명: 비트코인 (BTC)\n- 현재가: {price}원\n- 상승률: {rate:.2f}%\n- 예상 수익률: 5~7%\n- 예상 소요 시간: 30분\n- 추천 이유: 체결량 급증 + 거래대금 유입\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
            )

        time.sleep(10)

# 급락포착
def detect_price_drop():
    market = "KRW-BTC"
    while True:
        price = get_current_price(market)
        if not price:
            time.sleep(10)
            continue

        now = time.time()
        history = price_history.setdefault(market, [])
        history.append((now, price))
        price_history[market] = [(t, p) for t, p in history if now - t <= 120]

        base_time, base_price = price_history[market][0]
        rate = ((price - base_price) / base_price) * 100

        if rate <= -5.0 and now - last_alert_time.get(market + "_drop", 0) > 1800:
            last_alert_time[market + "_drop"] = now
            send_telegram_alert(
                f"[급락포착 💧]\n- 코인명: 비트코인 (BTC)\n- 현재가: {price}원\n- 하락률: {rate:.2f}%\n- 예상 반등 가능성: 중간 이상\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
            )

        time.sleep(10)

# 스윙포착
def detect_swing_entry():
    market = "KRW-BTC"
    while True:
        price = get_current_price(market)
        if not price:
            time.sleep(10)
            continue

        now = time.time()
        history = price_history.setdefault(market, [])
        history.append((now, price))
        price_history[market] = [(t, p) for t, p in history if now - t <= 600]

        base_time, base_price = price_history[market][0]
        rate = ((price - base_price) / base_price) * 100

        if rate >= 1.0 and now - last_alert_time.get(market + "_swing", 0) > 1800:
            last_alert_time[market + "_swing"] = now
            send_telegram_alert(
                f"[스윙포착 🌊]\n- 코인명: 비트코인 (BTC)\n- 현재가: {price}원\n- 상승률: {rate:.2f}%\n- 예상 수익률: 5~10%\n- 예상 소요 시간: 2시간\n- 추천 이유: 체결량 + 거래대금 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
            )

        time.sleep(10)

# 서버 실행
if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_price_surge, daemon=True).start()
    threading.Thread(target=detect_price_drop, daemon=True).start()
    threading.Thread(target=detect_swing_entry, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
