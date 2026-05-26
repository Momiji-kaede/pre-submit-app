from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from database import init_db, get_user, create_user

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# データベース初期化
init_db(app)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
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
            return redirect(url_for('dashboard'))
        else:
            error = 'ユーザー名またはパスワードが正しくありません'
            return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not username or not password:
            error = 'ユーザー名とパスワードを入力してください'
            return render_template('register.html', error=error)
        
        if password != password_confirm:
            error = 'パスワードが一致しません'
            return render_template('register.html', error=error)
        
        if get_user(username):
            error = 'このユーザー名は既に使用されています'
            return render_template('register.html', error=error)
        
        hashed_password = generate_password_hash(password)
        create_user(username, hashed_password)
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
