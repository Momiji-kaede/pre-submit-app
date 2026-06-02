from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ===== ユーザー関連 =====
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120))  # 氏名
    student_id = db.Column(db.String(20), unique=True)  # 学籍番号
    grade = db.Column(db.Integer)  # 学年
    class_number = db.Column(db.String(50))  # 組
    student_number = db.Column(db.Integer)  # 出席番号
    role = db.Column(db.String(20), nullable=False)  # teacher, student, assistant
    is_system_admin = db.Column(db.Boolean, default=False)  # システム管理者権限
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

# ===== 年度管理 =====
class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, unique=True)  # 2024, 2025など
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AcademicYear {self.year}>'

# ===== 授業情報 =====
class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(200), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Course {self.course_name}>'

# ===== 授業に登録した学生 =====
class CourseEnrollment(db.Model):
    __tablename__ = 'course_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseEnrollment {self.course_id}-{self.student_id}>'

# ===== 課題情報 =====
class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecture_number = db.Column(db.Integer, nullable=False)  # 第1回～第15回
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # 登録日・公開日設定
    registration_date = db.Column(db.DateTime, nullable=False)  # 課題登録日
    public_start_date = db.Column(db.DateTime, nullable=False)  # 公開開始日
    public_end_date = db.Column(db.DateTime, nullable=False)    # 公開終了日
    is_published = db.Column(db.Boolean, default=False)  # 切り替え可能
    
    # 締め切り
    deadline = db.Column(db.DateTime, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

# ===== 提出管理 =====
class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(500))  # 元のファイル名
    submission_number = db.Column(db.Integer, default=1)  # 1回目、2回目など
    is_latest = db.Column(db.Boolean, default=True)  # 最新の提出か
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, default=False)  # 遅延フラグ
    message_to_teacher = db.Column(db.Text)  # 学生から教員へのメッセージ
    is_partial = db.Column(db.Boolean, default=False)  # 部分提出フラグ
    
    def __repr__(self):
        return f'<Submission {self.assignment_id}-{self.student_id}>'

# ===== 提出後URL =====
class SubmissionURL(db.Model):
    __tablename__ = 'submission_urls'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    url_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubmissionURL {self.url_token}>'

# ===== ルーブリック =====
class Rubric(db.Model):
    __tablename__ = 'rubrics'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)  # 採点項目名
    max_score = db.Column(db.Integer, nullable=False)  # 最高点
    description = db.Column(db.Text)  # 説明
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Rubric {self.item_name}>'

# ===== 採点管理 =====
class Grading(db.Model):
    __tablename__ = 'gradings'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    score = db.Column(db.Integer)  # 点数
    comment = db.Column(db.Text)  # コメント
    is_public = db.Column(db.Boolean, default=False)  # 公開/非公開
    graded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Grading {self.assignment_id}-{self.student_id}>'

# ===== 提出ファイル =====
class SubmissionFile(db.Model):
    __tablename__ = 'submission_files'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    server_filename = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # ファイルサイズ（バイト）
    is_webgl = db.Column(db.Boolean, default=False)  # WebGLフラグ
    is_pdf = db.Column(db.Boolean, default=False)  # PDFフラグ
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubmissionFile {self.original_filename}>'

# ===== データベース初期化 =====
def init_db(app):
    """データベースを初期化"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

# ===== ユーザー関連の関数 =====
def get_user(username):
    """ユーザー名からユーザーを取得"""
    user = User.query.filter_by(username=username).first()
    if user:
        return {
            'id': user.id,
            'username': user.username,
            'password': user.password,
            'role': user.role,
            'is_system_admin': user.is_system_admin,
            'full_name': user.full_name,
            'student_id': user.student_id
        }
    return None

def create_user(username, email, password, role, is_system_admin=False, full_name=None, student_id=None, grade=None, class_number=None, student_number=None):
    """新しいユーザーを作成"""
    user = User(
        username=username,
        email=email,
        password=password,
        role=role,
        is_system_admin=is_system_admin,
        full_name=full_name,
        student_id=student_id,
        grade=grade,
        class_number=class_number,
        student_number=student_number
    )
    db.session.add(user)
    db.session.commit()
    return user

def get_all_students():
    """全学生を取得"""
    return User.query.filter_by(role='student').all()

def get_all_assistants():
    """全補助学生を取得"""
    return User.query.filter_by(role='assistant').all()

def delete_user(user_id):
    """ユーザーを削除"""
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False

# ===== 年度関連の関数 =====
def get_or_create_academic_year(year):
    """年度を取得または作成"""
    academic_year = AcademicYear.query.filter_by(year=year).first()
    if not academic_year:
        academic_year = AcademicYear(year=year)
        db.session.add(academic_year)
        db.session.commit()
    return academic_year

# ===== 授業関連の関数 =====
def create_course(course_name, academic_year_id, teacher_id, description=None):
    """授業を作成"""
    course = Course(course_name=course_name, academic_year_id=academic_year_id, teacher_id=teacher_id, description=description)
    db.session.add(course)
    db.session.commit()
    return course

def get_course(course_id):
    """授業情報を取得"""
    return Course.query.get(course_id)

# ===== 課題関連の関数 =====
def create_assignment(course_id, lecture_number, title, description, registration_date, public_start_date, public_end_date, deadline):
    """課題を作成"""
    assignment = Assignment(
        course_id=course_id,
        lecture_number=lecture_number,
        title=title,
        description=description,
        registration_date=registration_date,
        public_start_date=public_start_date,
        public_end_date=public_end_date,
        deadline=deadline,
        is_published=False
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment

def get_assignment(assignment_id):
    """課題情報を取得"""
    return Assignment.query.get(assignment_id)

def get_course_assignments(course_id):
    """授業の全課題を取得"""
    return Assignment.query.filter_by(course_id=course_id).all()

# ===== 提出関連の関数 =====
def create_submission(assignment_id, student_id, file_path, original_filename=None, message=None):
    """提出を作成"""
    # 最新の提出番号を取得
    latest_submission = Submission.query.filter_by(assignment_id=assignment_id, student_id=student_id, is_latest=True).first()
    
    submission_number = 1
    if latest_submission:
        latest_submission.is_latest = False
        submission_number = latest_submission.submission_number + 1
    
    submission = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        file_path=file_path,
        original_filename=original_filename,
        submission_number=submission_number,
        is_latest=True,
        message_to_teacher=message
    )
    db.session.add(submission)
    db.session.commit()
    return submission

def get_student_submission(assignment_id, student_id):
    """学生の最新提出を取得"""
    return Submission.query.filter_by(assignment_id=assignment_id, student_id=student_id, is_latest=True).first()

def get_submission_history(assignment_id, student_id):
    """提出履歴を取得"""
    return Submission.query.filter_by(assignment_id=assignment_id, student_id=student_id).order_by(Submission.submitted_at.desc()).all()

# ===== ルーブリック関連の関数 =====
def create_rubric(assignment_id, item_name, max_score, description=None):
    """ルーブリック項目を作成"""
    rubric = Rubric(assignment_id=assignment_id, item_name=item_name, max_score=max_score, description=description)
    db.session.add(rubric)
    db.session.commit()
    return rubric

def get_assignment_rubrics(assignment_id):
    """課題のルーブリック項目を取得"""
    return Rubric.query.filter_by(assignment_id=assignment_id).all()

# ===== 採点関連の関数 =====
def create_grading(assignment_id, student_id, rubric_id, score, comment=None, is_public=False):
    """採点を作成"""
    grading = Grading(
        assignment_id=assignment_id,
        student_id=student_id,
        rubric_id=rubric_id,
        score=score,
        comment=comment,
        is_public=is_public
    )
    db.session.add(grading)
    db.session.commit()
    return grading

def get_student_grades(assignment_id, student_id):
    """学生の採点を取得"""
    return Grading.query.filter_by(assignment_id=assignment_id, student_id=student_id).all()

def get_student_total_score(assignment_id, student_id):
    """学生の合計点を計算"""
    grades = get_student_grades(assignment_id, student_id)
    return sum([g.score for g in grades if g.score is not None])
