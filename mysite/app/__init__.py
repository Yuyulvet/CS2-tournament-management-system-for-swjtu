# app/__init__.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from model import Base
from flask_wtf.csrf import CSRFProtect
import os

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # 使用环境变量获取配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads/team_avatars')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

    # 数据库配置
    # 优先使用环境变量中的数据库 URL，如果没有则使用 SQLite
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///my_database.db')
    
    # 如果是 MySQL 数据库（比如在 Railway 上）
    if DATABASE_URL.startswith('mysql'):
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
    else:
        # 本地开发使用 SQLite
        engine = create_engine(DATABASE_URL)

    # 创建所有表   
    Base.metadata.create_all(engine)

    # 创建会话工厂
    Session = scoped_session(sessionmaker(bind=engine))
    app.db_session = Session

    # 注册蓝图
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .view import main_bp
    app.register_blueprint(main_bp)

    # 初始化 CSRF 保护
    csrf.init_app(app)

    # 确保上传目录存在
    upload_dir = os.path.join(app.root_path, 'static/uploads/team_avatars')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    # 请求结束时移除数据库会话
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()

    # 错误处理
    @app.errorhandler(404)
    def page_not_found(e):
        return "页面未找到", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return "服务器内部错误", 500

    return app
