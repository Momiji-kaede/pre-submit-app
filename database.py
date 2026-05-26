from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

def init_db(app):
    """データベースを初期化"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

def get_user(username):
    """ユーザー名からユーザーを取得"""
    user = User.query.filter_by(username=username).first()
    if user:
        return {'id': user.id, 'username': user.username, 'password': user.password}
    return None

def create_user(username, password):
    """新しいユーザーを作成"""
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return user