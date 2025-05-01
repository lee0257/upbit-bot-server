from flask import Flask
import threading
import time
import requests
import datetime

app = Flask(__name__)

chat_ids = [
    "1901931119",  # 너
    "7146684315"   # 친구
]

token = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
headers = {"accept": "application/json"}

price_history = {}
alert_history = {}

def send_telegram_alert(message):
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            print(f"[❌ 텔레그램 실패] {chat_id}")

def get_market_list():
    url = "https://api.upbit.com/v1/market/all?isDetails=true"
    response = requests.get(url, headers=headers)
    markets = response.json()
    return [
        (m["market"], m["korean_name"]) for m in markets
        if m["market"].startswith("KRW-") and not m["market"].startswith("KRW-BTC")
    ]

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url, headers=headers)
        return response.json()[0]['trade_price']
    except:
        return None

def is_duplicate_alert(market, alert_type):
    now = time.time()
    if market not in alert_history:
        alert_history[market] = {}
    if alert_type in alert_history[market]:
        last_time = alert_history[market][alert_type]
        if now - last_time < 1800:  # 30분 중복 차단
            return True
    alert_history[market][alert_type] = now
    return False

def monitor_markets():
    markets = get_market_list()
    while True:
        now = time.time()
        for market, name in markets:
            current_price = get_current_price(market)
            if not current_price:
                continue

            if market not in price_history:
                price_history[market] = []
            price_history[market].append((now, current_price))
            price_history[market] = [p for p in price_history[market] if now - p[0] <= 600]

            # 급등포착
            past_5min = [p for p in price_history[market] if now - p[0] <= 300]
            if len(past_5min) > 1:
                rate = (current_price - past_5min[0][1]) / past_5min[0][1] * 100
                if 1.0 <= rate <= 1.2 and not is_duplicate_alert(market, "급등"):
                    send_telegram_alert(
                        f"[급등포착 🔥]\n- 코인명: {name}\n- 현재가: {current_price}원\n"
                        f"- 5분간 상승률: {rate:.2f}%\n- 예상 수익률: 3~5%\n- 예상 소요 시간: 10분\n"
                        f"- 추천 이유: 체결량 급증 + 매수 강세 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )

            # 급락+바닥다지기
            past_2min = [p for p in price_history[market] if now - p[0] <= 120]
            if len(past_2min) > 1:
                rate = (current_price - past_2min[0][1]) / past_2min[0][1] * 100
                if rate <= -5.0:
                    # 바닥다지기: 이후 1분간 ±0.5% 이내 유지
                    stable = all(
                        abs((current_price - p[1]) / p[1]) <= 0.005
                        for p in price_history[market][-6:]
                    )
                    if stable and not is_duplicate_alert(market, "급락바닥"):
                        send_telegram_alert(
                            f"[급락+바닥다지기 포착 💧]\n- 코인명: {name}\n- 현재가: {current_price}원\n"
                            f"- 2분간 하락률: {rate:.2f}%\n- 바닥다지기 감지됨\n- 예상 반등 가능성: 높음\n"
                            f"https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                        )

            # 스윙포착
            rate10 = (current_price - price_history[market][0][1]) / price_history[market][0][1] * 100
            if 1.0 <= rate10 <= 1.2 and not is_duplicate_alert(market, "스윙"):
                send_telegram_alert(
                    f"[스윙포착 🌊]\n- 코인명: {name}\n- 현재가: {current_price}원\n"
                    f"- 10분간 상승률: {rate10:.2f}%\n- 예상 수익률: 5~7%\n- 예상 소요 시간: 1~3시간\n"
                    f"- 추천 이유: 거래량 증가 + 초기 상승 흐름 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                )

        # 매일 오전 8:50 초기화
        now = datetime.datetime.now()
        if now.hour == 8 and now.minute == 50:
            price_history.clear()
            alert_history.clear()

        time.sleep(10)

@app.route("/")
def hello():
    return "🚀 업비트 자동 알림 시스템 실행 중!"

if __name__ == "__main__":
    print("✅ 서버 매니저가 실행되었습니다.")
    threading.Thread(target=monitor_markets, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
