from flask import Flask
import threading
import time
import requests
import datetime

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

# ✅ 텔레그램 대상 ID
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

# ✅ 업비트 시세 조회
headers = {"accept": "application/json"}
price_history = {}
cooldowns = {}

# 시총 상위 5개 제외
top5 = ["KRW-BTC", "KRW-ETH", "KRW-SOL", "KRW-XRP", "KRW-AVAX"]

def get_market_list():
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    res = requests.get(url)
    markets = res.json()
    return [m['market'] for m in markets if m['market'].startswith("KRW-") and m['market'] not in top5]

def get_current_price(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        res = requests.get(url, headers=headers)
        return res.json()[0]['trade_price']
    except:
        return None

def should_notify(market, tag):
    now = time.time()
    key = f"{market}_{tag}"
    last_time = cooldowns.get(key, 0)
    if now - last_time >= 600:
        cooldowns[key] = now
        return True
    return False

def detect_all():
    while True:
        markets = get_market_list()
        for market in markets:
            current_price = get_current_price(market)
            if current_price:
                now = time.time()
                price_history.setdefault(market, []).append((now, current_price))
                price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]

                oldest_time, oldest_price = price_history[market][0]
                rate = ((current_price - oldest_price) / oldest_price) * 100

                # ✅ 급등
                if rate >= 3 and now - oldest_time <= 300 and should_notify(market, "surge"):
                    msg = (
                        f"[급등포착 🔥]\n코인명: {market}\n현재가: {current_price}원\n5분간 상승률: {rate:.2f}%\n"
                        f"매수 추천가: {int(current_price*0.98)} ~ {int(current_price*1.01)}원\n"
                        f"목표 매도가: {int(current_price*1.03)}원 이상\n예상 수익률: 3%+\n예상 소요 시간: 5~10분\n추천 이유: 빠른 체결량 증가\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}\n[긴급추천]"
                    )
                    send_telegram_alert(msg)

                # ✅ 급감
                if rate <= -5 and now - oldest_time <= 180 and should_notify(market, "drop"):
                    msg = (
                        f"[급감포착 💧]\n코인명: {market}\n현재가: {current_price}원\n3분간 하락률: {rate:.2f}%\n"
                        f"하락 후 눌림목 포착 가능성\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )
                    send_telegram_alert(msg)

                # ✅ 스윙매매 초입
                if 0 < rate <= 2 and now - oldest_time <= 600 and should_notify(market, "swing"):
                    msg = (
                        f"[스윙포착 🌊]\n코인명: {market}\n현재가: {current_price}원\n10분 내 상승률: {rate:.2f}%\n"
                        f"예상 수익률: 5~15%\n보유기간: 1~3일\nhttps://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )
                    send_telegram_alert(msg)
        time.sleep(15)

if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")
    threading.Thread(target=detect_all, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)


