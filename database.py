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
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
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
    submission_number = db.Column(db.Integer, default=1)  # 1回目、2回目など
    is_latest = db.Column(db.Boolean, default=True)  # 最新の提出か
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, default=False)  # 遅延フラグ
    
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
        return {'id': user.id, 'username': user.username, 'password': user.password, 'role': user.role, 'is_system_admin': user.is_system_admin}
    return None

def create_user(username, email, password, role, is_system_admin=False):
    """新しいユーザーを作成"""
    user = User(username=username, email=email, password=password, role=role, is_system_admin=is_system_admin)
    db.session.add(user)
    db.session.commit()
    return user

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
def create_submission(assignment_id, student_id, file_path):
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
        submission_number=submission_number,
        is_latest=True
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
