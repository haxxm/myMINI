from flask import Flask, render_template

app = Flask(__name__)

@app.route('/') # 웹사이트의 기본 경로 (예: http://127.0.0.1:5000/)
def index():
    return render_template('index.html') # templates 폴더의 index.html 파일을 렌더링하여 반환

if __name__ == '__main__':
    app.run(debug=True) # 개발 모드로 Flask 앱 실행 (코드 변경 시 자동 재시작)