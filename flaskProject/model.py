# model.py
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash

# 创建基础类
Base = declarative_base()
# 使用 SQLAlchemy Enum 定义赛制选项
class TournamentFormatEnum:
    BO1 = 'bo1'
    BO3 = 'bo3'
    BO5 = 'bo5'

TournamentFormat = Enum(
    TournamentFormatEnum.BO1,
    TournamentFormatEnum.BO3,
    TournamentFormatEnum.BO5,
    name='tournament_format_enum'
)

# 使用 SQLAlchemy Enum 定义赛事状态选项
class TournamentStatusEnum:
    NOT_STARTED = 'not_started'
    REGISTRATION_OPEN = 'registration_open'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

TournamentStatus = Enum(
    TournamentStatusEnum.NOT_STARTED,
    TournamentStatusEnum.REGISTRATION_OPEN,
    TournamentStatusEnum.IN_PROGRESS,
    TournamentStatusEnum.COMPLETED,
    name='tournament_status_enum'
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 用户ID
    username = Column(String(50), unique=True, nullable=False)  # 用户名
    email = Column(String(100), unique=True, nullable=False)  # 电子邮件地址
    password_hash = Column(String(128), nullable=False)  # 加密存储的密码
    role = Column(String(20), nullable=False)  # 用户角色

    teams = relationship('Team', 
                        foreign_keys='Team.captain_id',  # 指定使用 captain_id 作为外键
                        backref='captain',  # 改变 backref 名称以避免混淆
                        lazy=True)

    def set_password(self, password):
        """Hashes the password and stores it in the password_hash field."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies a given password against the stored password hash."""
        return check_password_hash(self.password_hash, password)

# 定义 Teams 表
class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    avatar_url = Column(String(255))
    country = Column(String(20))
    captain_id = Column(Integer, ForeignKey('users.id'))  # 队长ID
    players = relationship("Player", back_populates="team")

# 定义 Tournaments 表
class Tournament(Base):
    __tablename__ = 'tournaments'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    location = Column(String(50))
    start_time = Column(DateTime, nullable=False)  # 新增字段：赛事开始时间
    status = Column(TournamentStatus, nullable=False, default=TournamentStatusEnum.NOT_STARTED)  # 新增字段：赛事状态
    matches = relationship("Match", back_populates="tournament")
    registrations = relationship("Registration", back_populates="tournament")

# 定义 Matches 表
class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    team1_id = Column(Integer, ForeignKey('teams.id'))
    team2_id = Column(Integer, ForeignKey('teams.id'))
    tournament_format = Column(TournamentFormat, nullable=False)
    match_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    overall_score = Column(String(10))  # 总比分 (例如: "2-1")
    winner_id = Column(Integer, ForeignKey('teams.id'))
    
    tournament = relationship("Tournament", back_populates="matches")
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    winner = relationship("Team", foreign_keys=[winner_id])
    maps = relationship("Map", back_populates="match", cascade="all, delete-orphan")

# 定义 Registrations 表
class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    tournament = relationship("Tournament", back_populates="registrations")
    team = relationship("Team")
    status = Column(String(20), default='pending')

# 定义 Schedules 表
class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    location = Column(String(50), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    score = Column(String(10))  # 新增字段，用于存储地图比分
    
    match = relationship("Match")

class Statistics(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")
    player = relationship("Player")
    tournament = relationship("Tournament")
    match = relationship("Match")

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    role = Column(String(50))  # 如 AWPer, Rifler, IGL 等
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="players")

# 在现有的模型定义中添加 Map 类
class Map(Base):
    __tablename__ = 'maps'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    name = Column(String(50))  # 地图名称
    score = Column(String(20))  # 比分 (例如: "16-14")
    winner = Column(String(20))  # 胜者 ("team1" 或 "team2")
    order = Column(Integer)  # 添加顺序字段

    match = relationship("Match", back_populates="maps")

print("Database created and data added successfully!")


