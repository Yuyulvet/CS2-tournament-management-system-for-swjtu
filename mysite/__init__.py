# app/__init__.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from model import Base
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads/team_avatars'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

    # 创建 SQLite 数据库引擎    
    engine = create_engine('sqlite:///my_database.db')

    # 创建所有表   
    Base.metadata.create_all(engine)

    # 创建会话工厂
    Session = scoped_session(sessionmaker(bind=engine))
    app.db_session = Session

    # 注册蓝图（添加 url_prefix）
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .view import main_bp
    app.register_blueprint(main_bp)

    # 初始化 CSRF 保护
    csrf.init_app(app)

    # 请求结束时移除数据库会话
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()

    return app

# 创建全局 app 实例
app = create_app()

# 添加 Vercel 所需的 handler 函数
def handler(event, context):
    return app(event['body'], event['headers'])
