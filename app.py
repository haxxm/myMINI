from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

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

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- 메인 페이지 라우트 ---
@app.route('/')
def index():
    if not current_user.is_authenticated:
        if 'free_trial_count' not in session:
            session['free_trial_count'] = 0
        MAX_FREE_TRIALS = 5
        remaining_trials = MAX_FREE_TRIALS - session['free_trial_count']
        return render_template('index.html', remaining_trials=remaining_trials, is_authenticated=False)
    else:
        return render_template('index.html', is_authenticated=True)

# --- 회원가입 라우트 ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user_username = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        existing_user_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

        if existing_user_username:
            flash('사용자명이 이미 존재합니다. 다른 사용자명을 선택해주세요.', 'danger')
            return redirect(url_for('register'))
        if existing_user_email:
            flash('이메일이 이미 사용 중입니다. 다른 이메일을 사용해주세요.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('회원가입이 완료되었습니다! 이제 로그인할 수 있습니다.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- 로그인 라우트 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = True if request.form.get('remember_me') else False

        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('로그인되었습니다!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('로그인 실패. 사용자명 또는 비밀번호를 확인해주세요.', 'danger')
    return render_template('login.html')

# --- 로그아웃 라우트 ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))

# --- 대시보드 라우트 (로그인 필요) ---
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# --- PPT to PDF 변환 라우트 ---
@app.route('/convert', methods=['POST'])
def convert():
    MAX_FREE_TRIALS = 5

    if not current_user.is_authenticated:
        if 'free_trial_count' not in session:
            session['free_trial_count'] = 0

        if session['free_trial_count'] >= MAX_FREE_TRIALS:
            flash(f'무료 사용 횟수({MAX_FREE_TRIALS}회)를 모두 소진했습니다. 더 많은 변환을 위해 로그인하거나 유료 버전을 구매해주세요.', 'danger')
            return redirect(url_for('index'))

        session['free_trial_count'] += 1

    if 'file' not in request.files:
        flash('파일이 업로드되지 않았습니다.', 'danger')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('파일을 선택해주세요.', 'danger')
        return redirect(url_for('index'))

    if file:
        filename = file.filename
        if not (filename.endswith('.ppt') or filename.endswith('.pptx')):
            flash('PPT 파일 (.ppt, .pptx)만 업로드할 수 있습니다.', 'danger')
            return redirect(url_for('index'))

        unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        converted_pdf_filename = os.path.splitext(unique_filename)[0] + '.pdf'
        converted_pdf_filepath = os.path.join(app.config['CONVERTED_FOLDER'], converted_pdf_filename)

        # --- 임시 더미 PDF 파일 생성 (실제 변환 기능이 없을 때 테스트용) ---
        try:
            with open(converted_pdf_filepath, 'w') as f:
                f.write(f"This is a dummy PDF for {filename}. (Converted from PPT to PDF)\n")
                f.write(f"Original file: {filename}\n")
                f.write(f"Converted at: {os.path.basename(converted_pdf_filepath)}\n")
            print(f"DEBUG: Dummy PDF created at {converted_pdf_filepath}")
        except Exception as e:
            flash(f'더미 PDF 생성 중 오류 발생: {e}', 'danger')
            os.remove(filepath)
            return redirect(url_for('index'))

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
    converted_file_info = session.pop('converted_file_info', None)

    if not converted_file_info:
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
    filepath = os.path.join(app.config['CONVERTED_FOLDER'], filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    else:
        flash('요청하신 파일을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('index'))

# --- 새로운 기능: 스크립트 생성 시작 (키워드 선택) ---
@app.route('/script_generator/keywords', methods=['GET', 'POST'])
def keyword_select():
    # 예시 키워드 목록
    keywords = [
        '인공지능', '머신러닝', '데이터 과학', '클라우드 컴퓨팅', '사물 인터넷',
        '블록체인', '가상현실', '증강현실', '로봇공학', '양자 컴퓨팅'
    ]
    if request.method == 'POST':
        selected_keywords = request.form.getlist('keywords') # 여러 개 선택 가능
        if not selected_keywords:
            flash('키워드를 하나 이상 선택해주세요.', 'danger')
            return redirect(url_for('keyword_select'))
        
        session['selected_keywords'] = selected_keywords
        flash(f'선택된 키워드: {", ".join(selected_keywords)}', 'success')
        return redirect(url_for('script_option')) # 다음 단계로 이동
    
    return render_template('keyword_select.html', keywords=keywords)

# --- 새로운 기능: 스크립트 옵션 선택 (서론/본론/결론) ---
@app.route('/script_generator/options', methods=['GET', 'POST'])
def script_option():
    selected_keywords = session.get('selected_keywords')
    if not selected_keywords:
        flash('먼저 키워드를 선택해주세요.', 'danger')
        return redirect(url_for('keyword_select'))

    if request.method == 'POST':
        intro_option = request.form.get('intro_option')
        body_option = request.form.get('body_option')
        conclusion_option = request.form.get('conclusion_option')

        # 선택된 옵션들을 세션에 저장
        session['script_options'] = {
            'intro': intro_option,
            'body': body_option,
            'conclusion': conclusion_option
        }
        flash('스크립트 옵션이 저장되었습니다.', 'success')
        return redirect(url_for('script_result')) # 다음 단계로 이동

    # 예시 옵션들
    intro_options = ['흥미로운 질문으로 시작', '최신 트렌드 언급', '문제 제기']
    body_options = ['사례 연구 포함', '기술적 설명 강조', '미래 전망 제시']
    conclusion_options = ['핵심 요약 및 제언', '청중에게 질문 던지기', '긍정적 비전 제시']

    return render_template('script_option.html', 
                           selected_keywords=selected_keywords,
                           intro_options=intro_options,
                           body_options=body_options,
                           conclusion_options=conclusion_options)

# --- 새로운 기능: 완성된 대본 보여주기 ---
@app.route('/script_generator/result')
def script_result():
    selected_keywords = session.get('selected_keywords')
    script_options = session.get('script_options')

    if not selected_keywords or not script_options:
        flash('스크립트 생성에 필요한 정보가 부족합니다. 다시 시작해주세요.', 'danger')
        return redirect(url_for('keyword_select'))

    # --- 대본 생성 로직 (PLACEHOLDER) ---
    # 실제로는 여기에 LLM API 호출 등을 통해 대본을 생성하는 코드가 들어갑니다.
    # 여기서는 선택된 키워드와 옵션을 기반으로 간단한 더미 대본을 생성합니다.
    generated_script = f"""
    --- 대본 시작 ---

    **서론:**
    선택된 서론 옵션: "{script_options.get('intro', '없음')}"
    오늘 우리는 "{', '.join(selected_keywords)}"에 대해 이야기할 것입니다.

    **본론:**
    선택된 본론 옵션: "{script_options.get('body', '없음')}"
    "{', '.join(selected_keywords)}"의 핵심 개념과 중요성을 설명합니다.
    관련 사례를 들어 내용을 구체화합니다.

    **결론:**
    선택된 결론 옵션: "{script_options.get('conclusion', '없음')}"
    "{', '.join(selected_keywords)}"에 대한 논의를 요약하고, 미래 방향성을 제시합니다.

    --- 대본 끝 ---
    """
    
    # 세션 정보는 결과 페이지를 보여준 후 삭제 (선택 사항)
    # session.pop('selected_keywords', None)
    # session.pop('script_options', None)

    return render_template('script_result.html', 
                           generated_script=generated_script,
                           selected_keywords=selected_keywords,
                           script_options=script_options)


# --- 데이터베이스 생성 (최초 1회만 실행) ---
if __name__ == '__main__':
    with app.app_context():
       db.create_all()
    app.run(debug=True)
