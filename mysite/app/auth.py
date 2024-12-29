from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, jsonify, flash
from model import User,Team,Base
import bcrypt
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from werkzeug.exceptions import BadRequest
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf.exempt  # 对注册路由豁免 CSRF 保护
def register():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "无效的请求数据"}), 400

            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')

            # 验证必填字段
            if not all([username, email, password, role]):
                return jsonify({"error": "所有字段都必须填写"}), 400

            if role not in ['participant', 'manager']:
                return jsonify({"error": "无效的角色选择"}), 400

            # 修改数据库会话的获取方式
            db_session = current_app.db_session

            try:
                # 检查用户名是否已存在
                if db_session.query(User).filter_by(username=username).first():
                    return jsonify({"error": "用户名已存在"}), 400

                # 检查邮箱是否已存在
                if db_session.query(User).filter_by(email=email).first():
                    return jsonify({"error": "邮箱已被注册"}), 400

                # 创建新用户
                new_user = User(
                    username=username,
                    email=email,
                    role=role
                )
                new_user.set_password(password)

                db_session.add(new_user)
                db_session.commit()
                
                return jsonify({"message": "注册成功"}), 200

            except Exception as e:
                db_session.rollback()
                return jsonify({"error": f"注册失败：{str(e)}"}), 500

        except Exception as e:
            return jsonify({"error": f"服务器错误：{str(e)}"}), 500

    return render_template('register.html')


def validate_user(db_session, username, password):
    user = db_session.query(User).filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        db_session = current_app.db_session
        user = db_session.query(User).filter_by(username=username).first()

        if user and user.check_password(password) and user.role == role:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = role
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('用户名或密码错误，或角色选择有误', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('main.home'))