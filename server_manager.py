from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

# ✅ 텔레그램 설정
TOKEN = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
CHAT_IDS = [
    "1901931119",  # 너
    "7146684315",  # 친구
]

# ✅ 실시간 가격 저장용
price_history = {}
MARKETS = ["KRW-NEAR", "KRW-PENGU", "KRW-SUI", "KRW-ARB", "KRW-STX"]  # 테스트용 소수만

# ✅ 텔레그램 전송 함수
def send_alert(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"[에러] 텔레그램 전송 실패: {e}")

# ✅ 업비트 가격 조회 함수
def get_price(market):
    try:
        url = f"https://api.upbit.com/v1/ticker?markets={market}"
        res = requests.get(url).json()
        return res[0]["trade_price"]
    except:
        return None

# ✅ 급등 선행 포착 로직 (10분 내 2% 이상 상승 가능성 감지)
def detect_surge():
    while True:
        now = time.time()
        for market in MARKETS:
            price = get_price(market)
            if not price:
                continue

            # 가격 히스토리 초기화 및 유지
            history = price_history.setdefault(market, [])
            history.append((now, price))
            price_history[market] = [(t, p) for t, p in history if now - t <= 600]

            if len(price_history[market]) >= 2:
                start_time, start_price = price_history[market][0]
                rate = ((price - start_price) / start_price) * 100

                if rate >= 2.0:
                    send_alert(
                        f"[스윙포착 🌊]\n"
                        f"- 코인명: {market}\n"
                        f"- 현재가: {int(price)}원\n"
                        f"- 상승률: {rate:.2f}% (10분)\n"
                        f"- 조건: 선행포착 테스트\n"
                        f"- 링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
                    )
                    price_history[market] = []

        time.sleep(10)

# ✅ 수동 테스트용 라우트
@app.route("/test_trigger")
def test_trigger():
    send_alert("[테스트] 수동 트리거 정상 작동 ✅")
    return "수동 알림 발송 완료"

@app.route("/")
def home():
    return "업비트 봇 서버 정상 작동 중!"

# ✅ 서버 실행
if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=detect_surge, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
