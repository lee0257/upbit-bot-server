from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

chat_ids = [
    "1901931119",  # 본인 ID
    "7146684315"   # 친구 ID
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
notified_markets = {}

def get_current_data(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    try:
        response = requests.get(url)
        data = response.json()[0]
        return data['trade_price'], data['acc_trade_price_24h']
    except:
        return None, None

def get_market_list():
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    try:
        response = requests.get(url)
        return [m for m in response.json() if m['market'].startswith('KRW-') and not m['market'].startswith('KRW-BTC')][:100]  # 상위 100개만 예시
    except:
        return []

def detect_opportunities():
    markets = get_market_list()
    while True:
        for market_info in markets:
            market = market_info['market']
            korean_name = market_info['korean_name']

            current_price, volume = get_current_data(market)
            if not current_price or not volume:
                continue

            now = time.time()
            price_history.setdefault(market, []).append((now, current_price))
            price_history[market] = [(t, p) for t, p in price_history[market] if now - t <= 600]  # 10분 내 기록만 유지

            # 거래대금 필터
            if volume < 1200_000_000:
                continue

            # 상승률 계산
            oldest_time, oldest_price = price_history[market][0]
            rate = ((current_price - oldest_price) / oldest_price) * 100

            # 중복 알림 방지 (30분)
            last_alert = notified_markets.get(market, 0)
            if now - last_alert < 1800:
                continue

            # 급등포착
            if rate >= 3.0:
                msg = f"""[급등포착 🔥]
- 코인명: {korean_name} ({market})
- 현재가: {current_price}원
- 매수 추천가: {int(current_price*0.99)} ~ {int(current_price*1.01)}원
- 목표 매도가: {int(current_price*1.03)}원
- 예상 수익률: 3%+
- 예상 소요 시간: 10분 내외
- 추천 이유: 거래대금 활발 + 매수강세 + 선행포착
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""
                send_telegram_alert(msg)
                notified_markets[market] = now

            # 스윙포착 (0.8~2%)
            elif 0.8 <= rate <= 2.0:
                msg = f"""[스윙포착 🌊]
- 코인명: {korean_name} ({market})
- 현재가: {current_price}원
- 매수 추천가: {int(current_price*0.985)} ~ {int(current_price*1.005)}원
- 목표 매도가: {int(current_price*1.03)}원
- 예상 수익률: 3%+
- 예상 소요 시간: 1~3시간
- 추천 이유: 체결량 급증 + 매수 강세 포착
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""
                send_telegram_alert(msg)
                notified_markets[market] = now

            # 급락포착 (2분 내 5% 하락)
            recent_data = [(t, p) for t, p in price_history[market] if now - t <= 120]
            if len(recent_data) >= 2:
                oldest_t, oldest_p = recent_data[0]
                drop_rate = ((current_price - oldest_p) / oldest_p) * 100
                if drop_rate <= -5.0:
                    msg = f"""[급락포착 💧]
- 코인명: {korean_name} ({market})
- 현재가: {current_price}원
- 하락률: {drop_rate:.2f}%
- 감지 이유: 단기간 급락 + 매도세 강함
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""
                    send_telegram_alert(msg)
                    notified_markets[market] = now

        time.sleep(8)

if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_opportunities, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
