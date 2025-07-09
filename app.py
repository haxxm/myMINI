from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os # 파일 경로 관리를 위해 추가
import uuid # 비회원 세션 관리를 위해 추가

app = Flask(__name__)

# Flask 앱 설정
app.config['SECRET_KEY'] = 'your_super_secret_key' # 세션을 위한 비밀 키 (아주 중요! 실제 배포 시에는 복잡하고 예측 불가능한 문자열로 변경하세요.)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # SQLite 데이터베이스 파일 경로
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 변경 사항 추적 비활성화 (성능 향상)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # 로그인 필요 시 리다이렉트할 라우트 이름

# 업로드 및 변환된 파일을 저장할 폴더 설정
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # 폴더 없으면 생성
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# 사용자 모델 정의
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Flask-Login의 사용자 로더 함수
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) # Flask 2.3+ 부터는 get()을 사용

# --- 메인 페이지 라우트 ---
@app.route('/')
def index():
    # 비회원 사용량 추적을 위한 세션 초기화 및 전달
    # 현재 로그인된 사용자가 아니라면, 세션에 'free_trial_count'를 확인하거나 초기화
    if not current_user.is_authenticated:
        if 'free_trial_count' not in session:
            session['free_trial_count'] = 0
        # 최대 무료 사용 횟수
        MAX_FREE_TRIALS = 5
        remaining_trials = MAX_FREE_TRIALS - session['free_trial_count']
        return render_template('index.html', remaining_trials=remaining_trials, is_authenticated=False)
    else:
        # 로그인된 사용자라면 제한 없음 (또는 다른 제한 정책)
        return render_template('index.html', is_authenticated=True)

# --- 회원가입 라우트 ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: # 이미 로그인되어 있다면 대시보드로 리다이렉트
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # 사용자명 또는 이메일이 이미 존재하는지 확인
        existing_user_username = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        existing_user_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

        if existing_user_username:
            flash('사용자명이 이미 존재합니다. 다른 사용자명을 선택해주세요.', 'danger')
            return redirect(url_for('register'))
        if existing_user_email:
            flash('이메일이 이미 사용 중입니다. 다른 이메일을 사용해주세요.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password) # 비밀번호 해싱
        db.session.add(new_user)
        db.session.commit()
        flash('회원가입이 완료되었습니다! 이제 로그인할 수 있습니다.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- 로그인 라우트 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # 이미 로그인되어 있다면 대시보드로 리다이렉트
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = True if request.form.get('remember_me') else False # 'remember me' 체크박스

        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('로그인되었습니다!', 'success')
            # 다음 페이지로 이동해야 할 경우 (예: 로그인 후 원래 가려던 페이지로)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard')) # 로그인 후 이동할 페이지 (dashboard 예시)
        else:
            flash('로그인 실패. 사용자명 또는 비밀번호를 확인해주세요.', 'danger')
    return render_template('login.html')

# --- 로그아웃 라우트 ---
@app.route('/logout')
@login_required # 로그인된 사용자만 접근 가능
def logout():
    logout_user()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index')) # 로그아웃 후 메인 페이지로 이동

# --- 대시보드 라우트 (로그인 필요) ---
@app.route('/dashboard')
@login_required # 이 페이지는 로그인된 사용자만 접근할 수 있습니다.
def dashboard():
    return render_template('dashboard.html')

# --- Word to PDF 변환 라우트 ---
@app.route('/convert', methods=['POST'])
def convert():
    MAX_FREE_TRIALS = 5

    # 1. 사용량 제한 확인
    if not current_user.is_authenticated:
        # 비회원인 경우
        if 'free_trial_count' not in session:
            session['free_trial_count'] = 0

        if session['free_trial_count'] >= MAX_FREE_TRIALS:
            flash(f'무료 사용 횟수({MAX_FREE_TRIALS}회)를 모두 소진했습니다. 더 많은 변환을 위해 로그인하거나 유료 버전을 구매해주세요.', 'danger')
            return redirect(url_for('index')) # 또는 로그인/결제 페이지로 리다이렉트

        session['free_trial_count'] += 1 # 사용 횟수 증가

    # 2. 파일 처리
    if 'file' not in request.files:
        flash('파일이 업로드되지 않았습니다.', 'danger')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('파일을 선택해주세요.', 'danger')
        return redirect(url_for('index'))

    if file:
        # 파일 확장자 검사 (Word 파일만 허용)
        filename = file.filename
        if not (filename.endswith('.doc') or filename.endswith('.docx')):
            flash('Word 파일 (.doc, .docx)만 업로드할 수 있습니다.', 'danger')
            return redirect(url_for('index'))

        # 안전한 파일명 생성 및 저장
        unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1] # 고유한 파일명
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # 3. Word to PDF 변환 (이 부분이 핵심이자 가장 어려운 부분)
        converted_pdf_filename = os.path.splitext(unique_filename)[0] + '.pdf'
        converted_pdf_filepath = os.path.join(app.config['CONVERTED_FOLDER'], converted_pdf_filename)

        # --- 임시 더미 PDF 파일 생성 (실제 변환 기능이 없을 때 테스트용) ---
        try:
            with open(converted_pdf_filepath, 'w') as f:
                f.write(f"This is a dummy PDF for {filename}. (Converted from Word to PDF)\n")
                f.write(f"Original file: {filename}\n")
                f.write(f"Converted at: {os.path.basename(converted_pdf_filepath)}\n")
            print(f"DEBUG: Dummy PDF created at {converted_pdf_filepath}")
        except Exception as e:
            flash(f'더미 PDF 생성 중 오류 발생: {e}', 'danger')
            os.remove(filepath)
            return redirect(url_for('index'))

        # 4. 변환된 파일 정보를 세션에 저장하고 결과 페이지로 리다이렉트
        session['converted_file_info'] = {
            'original_filename': filename,
            'converted_filename': converted_pdf_filename
        }
        flash(f'"{filename}" 파일이 성공적으로 PDF로 변환되었습니다!', 'success')
        return redirect(url_for('converted_result'))

    flash('알 수 없는 오류가 발생했습니다.', 'danger')
    return redirect(url_for('index'))

# --- 변환 결과 페이지 라우트 ---
@app.route('/converted_result')
def converted_result():
    converted_file_info = session.pop('converted_file_info', None) # 세션에서 정보 가져오고 삭제

    if not converted_file_info:
        # 변환 정보가 없으면 메인 페이지로 리다이렉트
        flash('변환 결과 정보가 없습니다. 다시 시도해주세요.', 'danger')
        return redirect(url_for('index'))

    original_filename = converted_file_info['original_filename']
    converted_filename = converted_file_info['converted_filename']

    return render_template('converted_result.html',
                           original_filename=original_filename,
                           converted_filename=converted_filename)

# --- 변환된 파일 다운로드 라우트 ---
@app.route('/download/<filename>')
def download_file(filename):
    # 파일 경로가 안전한지 확인하는 로직 추가 필요 (os.path.join, send_from_directory 등)
    # 여기서는 간단히 join을 사용하지만, 실제로는 send_from_directory를 권장합니다.
    filepath = os.path.join(app.config['CONVERTED_FOLDER'], filename)
    
    # 파일이 존재하는지 확인
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    else:
        flash('요청하신 파일을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('index'))


# --- 데이터베이스 생성 (최초 1회만 실행) ---
if __name__ == '__main__':
    # 이 부분을 실행하기 전에 app.py 파일을 저장하고 터미널에서 `python app.py`를 실행하세요.
    # 그 후 앱을 종료하고 아래 두 줄의 주석을 해제하고 다시 실행하면 database가 생성됩니다.
    with app.app_context():
       db.create_all() # 데이터베이스 파일 및 테이블 생성
    app.run(debug=True)
