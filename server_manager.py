from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

# 텔레그램 정보
token = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
chat_ids = ["1901931119", "7146684315"]  # 사용자들

# 실시간 가격 저장소
price_data = {}

# 알림 중복 방지 타이머
last_alert_time = {}

# 업비트 코인 목록 (업데이트 가능)
markets = [
    "KRW-XRP", "KRW-NEAR", "KRW-ARB", "KRW-SUI", "KRW-HIFI", "KRW-SAND", "KRW-APT", "KRW-TRX",
    "KRW-STX", "KRW-MASK", "KRW-BCH", "KRW-ARDR", "KRW-AXS", "KRW-GLM", "KRW-GRT", "KRW-AVAX",
    "KRW-JST", "KRW-STRK", "KRW-STRAX", "KRW-POLYX", "KRW-ICX", "KRW-SUI", "KRW-PYTH", "KRW-ZETA"
]

# 한글명 매핑 (업비트 API 대체 불가 시 수동 관리)
market_names = {
    "KRW-XRP": "리플", "KRW-NEAR": "니어", "KRW-ARB": "아비트럼", "KRW-SUI": "수이", "KRW-HIFI": "하이파이",
    "KRW-SAND": "샌드박스", "KRW-APT": "앱토스", "KRW-TRX": "트론", "KRW-STX": "스택스", "KRW-MASK": "마스크네트워크",
    "KRW-BCH": "비트코인캐시", "KRW-ARDR": "아더", "KRW-AXS": "엑시인피니티", "KRW-GLM": "골렘",
    "KRW-GRT": "더그래프", "KRW-AVAX": "아발란체", "KRW-JST": "저스트", "KRW-STRK": "스타크넷",
    "KRW-STRAX": "스트라티스", "KRW-POLYX": "폴리메쉬", "KRW-ICX": "아이콘", "KRW-PYTH": "피스네트워크",
    "KRW-ZETA": "제타체인"
}

def send_alert(market, rate, current_price):
    now = time.time()
    if market in last_alert_time and now - last_alert_time[market] < 1800:  # 30분 중복 제한
        return
    last_alert_time[market] = now

    name = market_names.get(market, market)
    text = (
        f"[스윙포착 🌊]\n"
        f"- 코인명: {name} ({market})\n"
        f"- 현재가: {int(current_price)}원\n"
        f"- 상승률: {rate:.2f}% (10분)\n"
        f"- 조건: 거래대금 12억↑ + 선행포착\n"
        f"- 링크: https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
    )
    for chat_id in chat_ids:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": text})
        except:
            print(f"[알림 실패] {chat_id}")

def get_price(market):
    try:
        url = f"https://api.upbit.com/v1/ticker?markets={market}"
        res = requests.get(url).json()
        return res[0]["trade_price"], res[0]["acc_trade_price_24h"]
    except:
        return None, None

def monitor():
    while True:
        for market in markets:
            price, vol = get_price(market)
            if not price or not vol:
                continue
            if vol < 12_000_000_000:  # 거래대금 필터
                continue

            now = time.time()
            price_data.setdefault(market, []).append((now, price))
            price_data[market] = [(t, p) for t, p in price_data[market] if now - t <= 600]

            if len(price_data[market]) < 2:
                continue

            old_time, old_price = price_data[market][0]
            rate = ((price - old_price) / old_price) * 100

            # 선행포착: 2% 이상 오를 조짐을 1.5%~1.8% 구간에서 포착
            if 1.5 <= rate < 2.0:
                send_alert(market, rate, price)

        time.sleep(10)

@app.route("/")
def home():
    return "선행포착 시스템 실행 중!"

if __name__ == "__main__":
    print("서버 매니저 실행 중...")
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
