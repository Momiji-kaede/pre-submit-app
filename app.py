from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import zipfile
from io import BytesIO
from database import (
    db, init_db, User, AcademicYear, Course, CourseEnrollment, 
    Assignment, Submission, SubmissionURL,
    get_user, create_user, get_or_create_academic_year, 
    create_course, get_course, create_assignment, get_assignment,
    get_course_assignments, create_submission, get_student_submission,
    get_submission_history
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# ファイルアップロード設定
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'zip', 'exe', 'unity3d', 'bin', 'wasm', 'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# uploadsフォルダが存在しなければ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# データベース初期化
init_db(app)

def allowed_file(filename):
    """ファイル形式をチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_teacher():
    """ユーザーが教師かチェック"""
    return session.get('role') == 'teacher'

def is_admin():
    """ユーザーが管理者かチェック"""
    return session.get('role') == 'admin'

def is_student():
    """ユーザーが学生かチェック"""
    return session.get('role') == 'student'

def is_system_admin():
    """システム管理者権限をチェック"""
    return session.get('is_system_admin', False)

# ===== ログイン・登録関連 =====

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif role == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user(username)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['is_system_admin'] = user['is_system_admin']
            
            role = user['role']
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif role == 'student':
                return redirect(url_for('student_dashboard'))
        else:
            error = 'ユーザー名またはパスワードが正しくありません'
            return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not username or not email or not password:
            error = 'すべてのフィールドを入力してください'
            return render_template('register.html', error=error)
        
        if password != password_confirm:
            error = 'パスワードが一致しません'
            return render_template('register.html', error=error)
        
        if get_user(username):
            error = 'このユーザー名は既に使用されています'
            return render_template('register.html', error=error)
        
        hashed_password = generate_password_hash(password)
        # 新規登録は学生として登録
        create_user(username, email, hashed_password, 'student', False)
        
        flash('登録完了しました！ログインしてください', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===== 管理者用ルート =====

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('user_id') or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # 現在の年度一覧を取得
    academic_years = AcademicYear.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    students = User.query.filter_by(role='student').all()
    
    return render_template('admin/dashboard.html', 
                         academic_years=academic_years,
                         teachers=teachers,
                         students=students)

@app.route('/admin/academic-years', methods=['POST'])
def admin_create_academic_year():
    if not session.get('user_id') or not is_system_admin():
        return redirect(url_for('login'))
    
    year = request.form.get('year')
    description = request.form.get('description')
    
    try:
        academic_year = get_or_create_academic_year(int(year))
        if description:
            academic_year.description = description
            db.session.commit()
        flash(f'{year}年度を作成しました', 'success')
    except Exception as e:
        flash(f'エラー: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/teachers', methods=['POST'])
def admin_create_teacher():
    if not session.get('user_id') or not is_system_admin():
        return redirect(url_for('login'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_system_admin = request.form.get('is_system_admin') == 'on'
    
    try:
        if get_user(username):
            flash('このユーザー名は既に使用されています', 'error')
        else:
            hashed_password = generate_password_hash(password)
            create_user(username, email, hashed_password, 'teacher', is_system_admin)
            flash(f'教師 {username} を作成しました', 'success')
    except Exception as e:
        flash(f'エラー: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

# ===== 教師用ルート =====

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # 教師が担当する授業一覧
    courses = Course.query.filter_by(teacher_id=user_id).all()
    
    return render_template('teacher/dashboard.html', courses=courses)

@app.route('/teacher/course/<int:course_id>')
def teacher_course_detail(course_id):
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    course = get_course(course_id)
    if not course or course.teacher_id != session.get('user_id'):
        return redirect(url_for('teacher_dashboard'))
    
    assignments = get_course_assignments(course_id)
    enrollments = CourseEnrollment.query.filter_by(course_id=course_id).all()
    
    return render_template('teacher/course_detail.html',
                         course=course,
                         assignments=assignments,
                         enrollments=enrollments)

@app.route('/teacher/assignment/<int:assignment_id>')
def teacher_assignment_submissions(assignment_id):
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    assignment = get_assignment(assignment_id)
    if not assignment:
        return redirect(url_for('teacher_dashboard'))
    
    course = get_course(assignment.course_id)
    if course.teacher_id != session.get('user_id'):
        return redirect(url_for('teacher_dashboard'))
    
    # 提出状況を取得
    submissions = Submission.query.filter_by(assignment_id=assignment_id, is_latest=True).all()
    enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
    
    # 学生ごとの提出状況を整理
    submission_status = {}
    for enrollment in enrollments:
        student_id = enrollment.student_id
        student = User.query.get(student_id)
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student_id,
            is_latest=True
        ).first()
        
        is_late = False
        if submission:
            is_late = submission.submitted_at > assignment.deadline
        
        submission_status[student_id] = {
            'student': student,
            'submission': submission,
            'is_late': is_late
        }
    
    return render_template('teacher/assignment_submissions.html',
                         assignment=assignment,
                         course=course,
                         submission_status=submission_status)

@app.route('/teacher/students/<int:course_id>', methods=['POST'])
def teacher_register_student(course_id):
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    course = get_course(course_id)
    if not course or course.teacher_id != session.get('user_id'):
        return redirect(url_for('teacher_dashboard'))
    
    student_id = request.form.get('student_id')
    
    try:
        # 既に登録されているかチェック
        existing = CourseEnrollment.query.filter_by(
            course_id=course_id,
            student_id=student_id
        ).first()
        
        if existing:
            flash('この学生は既に登録されています', 'warning')
        else:
            enrollment = CourseEnrollment(course_id=course_id, student_id=student_id)
            db.session.add(enrollment)
            db.session.commit()
            flash('学生を登録しました', 'success')
    except Exception as e:
        flash(f'エラー: {str(e)}', 'error')
    
    return redirect(url_for('teacher_course_detail', course_id=course_id))

@app.route('/teacher/assignment/create/<int:course_id>', methods=['GET', 'POST'])
def teacher_create_assignment(course_id):
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    course = get_course(course_id)
    if not course or course.teacher_id != session.get('user_id'):
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        try:
            lecture_number = int(request.form.get('lecture_number'))
            title = request.form.get('title')
            description = request.form.get('description')
            registration_date = datetime.fromisoformat(request.form.get('registration_date'))
            public_start_date = datetime.fromisoformat(request.form.get('public_start_date'))
            public_end_date = datetime.fromisoformat(request.form.get('public_end_date'))
            deadline = datetime.fromisoformat(request.form.get('deadline'))
            
            assignment = create_assignment(
                course_id, lecture_number, title, description,
                registration_date, public_start_date, public_end_date, deadline
            )
            
            flash(f'課題「{title}」を作成しました', 'success')
            return redirect(url_for('teacher_course_detail', course_id=course_id))
        except Exception as e:
            flash(f'エラー: {str(e)}', 'error')
    
    return render_template('teacher/create_assignment.html', course=course)

@app.route('/teacher/assignment/<int:assignment_id>/toggle-publish', methods=['POST'])
def teacher_toggle_publish(assignment_id):
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    assignment = get_assignment(assignment_id)
    if not assignment:
        return redirect(url_for('teacher_dashboard'))
    
    course = get_course(assignment.course_id)
    if course.teacher_id != session.get('user_id'):
        return redirect(url_for('teacher_dashboard'))
    
    assignment.is_published = not assignment.is_published
    db.session.commit()
    
    status = '公開' if assignment.is_published else '非公開'
    flash(f'課題を{status}に変更しました', 'success')
    
    return redirect(url_for('teacher_course_detail', course_id=assignment.course_id))

@app.route('/teacher/course/<int:course_id>/download-zip')
def teacher_download_zip(course_id):
    if not session.get('user_id') or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    course = get_course(course_id)
    if not course or course.teacher_id != session.get('user_id'):
        return redirect(url_for('teacher_dashboard'))
    
    # ZIPファイルを作成
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        assignments = get_course_assignments(course_id)
        
        for assignment in assignments:
            submissions = Submission.query.filter_by(
                assignment_id=assignment.id,
                is_latest=True
            ).all()
            
            # 課題ごとのフォルダを作成
            folder_name = f"lecture_{assignment.lecture_number:02d}_{assignment.title}"
            
            for submission in submissions:
                if os.path.exists(submission.file_path):
                    student = User.query.get(submission.student_id)
                    file_name = f"{student.username}_{submission.submission_number}.zip"
                    
                    with open(submission.file_path, 'rb') as f:
                        zip_file.writestr(f"{folder_name}/{file_name}", f.read())
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{course.course_name}_{course.academic_year_id}.zip'
    )

# ===== 学生用ルート =====

@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('user_id') or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # 学生が登録している授業一覧
    enrollments = CourseEnrollment.query.filter_by(student_id=user_id).all()
    courses = [CourseEnrollment.query.get(e.id).course_id for e in enrollments]
    
    courses_data = Course.query.filter(Course.id.in_(courses)).all() if courses else []
    
    return render_template('student/dashboard.html', courses=courses_data)

@app.route('/student/course/<int:course_id>')
def student_course_assignments(course_id):
    if not session.get('user_id') or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # 登録確認
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id,
        student_id=user_id
    ).first()
    
    if not enrollment:
        return redirect(url_for('student_dashboard'))
    
    course = get_course(course_id)
    assignments = get_course_assignments(course_id)
    
    # 各課題の提出状況を確認
    assignment_data = []
    for assignment in assignments:
        submission = get_student_submission(assignment.id, user_id)
        assignment_data.append({
            'assignment': assignment,
            'submission': submission
        })
    
    return render_template('student/course_assignments.html',
                         course=course,
                         assignment_data=assignment_data)

@app.route('/student/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
def student_submit_assignment(assignment_id):
    if not session.get('user_id') or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    assignment = get_assignment(assignment_id)
    
    if not assignment:
        return redirect(url_for('student_dashboard'))
    
    course = get_course(assignment.course_id)
    
    # 登録確認
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course.id,
        student_id=user_id
    ).first()
    
    if not enrollment:
        return redirect(url_for('student_dashboard'))
    
    # 公開期間チェック
    now = datetime.utcnow()
    if not assignment.is_published or now < assignment.public_start_date or now > assignment.public_end_date:
        flash('この課題は現在提出できません', 'warning')
        return redirect(url_for('student_course_assignments', course_id=course.id))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('ファイルが選択されていません', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('ファイルが選択されていません', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('許可されていないファイル形式です', 'error')
            return redirect(request.url)
        
        try:
            # ファイルを保存
            filename = secure_filename(file.filename)
            unique_filename = f"{user_id}_{assignment_id}_{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # 提出を記録
            submission = create_submission(assignment_id, user_id, filepath)
            
            # 遅延チェック
            is_late = datetime.utcnow() > assignment.deadline
            submission.is_late = is_late
            db.session.commit()
            
            # 提出URL生成
            url_token = str(uuid.uuid4())
            submission_url = SubmissionURL(submission_id=submission.id, url_token=url_token)
            db.session.add(submission_url)
            db.session.commit()
            
            flash('ファイルを提出しました', 'success')
            return redirect(url_for('student_submission_url', url_token=url_token))
        except Exception as e:
            flash(f'エラー: {str(e)}', 'error')
    
    return render_template('student/submit_assignment.html',
                         assignment=assignment,
                         course=course)

@app.route('/submission/<url_token>')
def student_submission_url(url_token):
    submission_url = SubmissionURL.query.filter_by(url_token=url_token).first()
    
    if not submission_url:
        flash('無効なURLです', 'error')
        return redirect(url_for('login'))
    
    submission = Submission.query.get(submission_url.submission_id)
    assignment = get_assignment(submission.assignment_id)
    student = User.query.get(submission.student_id)
    
    return render_template('student/submission_url.html',
                         submission=submission,
                         assignment=assignment,
                         student=student,
                         url_token=url_token)

@app.route('/student/assignment/<int:assignment_id>/history')
def student_submission_history(assignment_id):
    if not session.get('user_id') or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    assignment = get_assignment(assignment_id)
    course = get_course(assignment.course_id)
    
    # 登録確認
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course.id,
        student_id=user_id
    ).first()
    
    if not enrollment:
        return redirect(url_for('student_dashboard'))
    
    history = get_submission_history(assignment_id, user_id)
    
    return render_template('student/submission_history.html',
                         assignment=assignment,
                         course=course,
                         history=history)

@app.route('/student/course/<int:course_id>/game')
def student_play_game(course_id):
    if not session.get('user_id') or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # 登録確認
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id,
        student_id=user_id
    ).first()
    
    if not enrollment:
        return redirect(url_for('student_dashboard'))
    
    course = get_course(course_id)
    
    return render_template('student/game_list.html', course=course)

# エラーハンドリング
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
