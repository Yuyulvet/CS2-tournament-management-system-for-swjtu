# app/__init__.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from model import Base
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# 创建全局变量
application = None
app = None

def create_app():
    global application, app  # 声明使用全局变量
    
    application = Flask(__name__)
    app = application  # 同时设置 app 变量
    
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads/team_avatars'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    engine = create_engine('sqlite:///my_database.db')
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

# 确保在模块级别创建应用实例
app = create_app()

def handler(event, context):
    return app.wsgi_app(event, context)
