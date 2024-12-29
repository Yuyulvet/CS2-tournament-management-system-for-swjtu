# app/__init__.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from model import Base
from flask_wtf.csrf import CSRFProtect
import os

csrf = CSRFProtect()

# 创建全局变量
application = None
app = None

def create_app():
    global application, app
    
    application = Flask(__name__)
    app = application
    
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads/team_avatars'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # 使用 Railway 提供的环境变量构建数据库 URL
    MYSQL_URL = f"mysql://root:{os.getenv('MYSQL_ROOT_PASSWORD')}@{os.getenv('MYSQLHOST')}:{os.getenv('MYSQLPORT')}/{os.getenv('MYSQL_DATABASE')}"
    
    # 创建 MySQL 引擎
    engine = create_engine(
        MYSQL_URL,
        pool_size=5,
        pool_recycle=3600,
        pool_pre_ping=True
    )
    
    Base.metadata.create_all(engine)
    
    Session = scoped_session(sessionmaker(bind=engine))
    app.db_session = Session
    
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .view import main_bp
    app.register_blueprint(main_bp)
    
    csrf.init_app(app)
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()
        
    return app

app = create_app()

def handler(event, context):
    return app.wsgi_app(event, context)
