from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "업비트 봇 서버 실행 중!"

if __name__ == "__main__":
    print("서버 매니저가 실행되었습니다.")
    app.run(host="0.0.0.0", port=8000)
