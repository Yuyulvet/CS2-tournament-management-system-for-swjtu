# view.py
from flask import Blueprint, session, redirect, url_for, render_template, request, current_app, flash, jsonify, abort
from model import User,Team, Tournament,Registration, Match, Schedule, Player, Statistics, Map
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from sqlalchemy.sql import func, desc
from sqlalchemy.orm import joinedload
from sqlalchemy import or_


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    role = session.get('role')
    
    # 获取数据库会话
    db_session = current_app.db_session
    
    if role == 'participant':
        # 获取用户的战队
        user_team = db_session.query(Team).filter_by(captain_id=user_id).first()
        
        if user_team:
            # 获取即将进行的比赛，包括地图信息
            upcoming_matches = db_session.query(Match).\
                filter(or_(Match.team1_id == user_team.id, Match.team2_id == user_team.id)).\
                filter(Match.match_time > datetime.now()).\
                options(joinedload(Match.maps)).\
                order_by(Match.match_time).all()
        else:
            upcoming_matches = []
            
        return render_template('dashboard.html',
                             role=role,
                             user_team=user_team,
                             upcoming_matches=upcoming_matches)
    
    elif role == 'manager':
        # 获取管理员需要的统计数据
        total_teams = db_session.query(Team).count()
        total_tournaments = db_session.query(Tournament).count()
        total_matches = db_session.query(Match).count()
        return render_template('dashboard.html', 
                            total_teams=total_teams,
                            total_tournaments=total_tournaments,
                            total_matches=total_matches,
                            role=role)
    else:
        return "Role not recognized", 403

@main_bp.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    user_id = session['user_id']
    user = db_session.query(User).filter_by(id=user_id).first()

    if request.method == 'POST':
        if 'update_profile' in request.form:
            # 处理编辑个人资料的表单
            username = request.form.get('username', user.username)
            email = request.form.get('email', user.email)

            # 检查用户名和邮箱是否被其他用户使用
            if db_session.query(User).filter(User.username == username, User.id != user_id).first():
                flash("Username already taken", 'error')
                return redirect(url_for('main.edit_profile'))
            if db_session.query(User).filter(User.email == email, User.id != user_id).first():
                flash("Email already registered", 'error')
                return redirect(url_for('main.edit_profile'))

            user.username = username
            user.email = email

            db_session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('main.edit_profile'))

        elif 'change_password' in request.form:
            # 处理更改密码的表单
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # 验证当前密码
            if not user.check_password(current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('main.edit_profile'))

            # 验证新密码和确认密码是否匹配
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return redirect(url_for('main.edit_profile'))

            # 更新密码
            user.set_password(new_password)
            db_session.commit()

            flash('Password updated successfully', 'success')
            return redirect(url_for('main.edit_profile'))

    return render_template('profile.html', user=user)


@main_bp.route('/system_management')
def system_management():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    return render_template('system_management.html')

@main_bp.route('/team_management')
def team_management():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    teams = db_session.query(Team).all()
    return render_template('team_management.html', teams=teams)

@main_bp.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    team = db_session.query(Team).filter_by(id=team_id).first()

    # 检查权限（管理员或战队队长）
    if session.get('role') != 'manager' and session.get('user_id') != team.captain_id:
        flash('没有权限编辑此战队', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        team.name = request.form.get('name', team.name)
        team.country = request.form.get('country', team.country)

        # 处理头像上传
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                team.avatar_url = url_for('static', filename=f'uploads/team_avatars/{filename}')

        # 处理队员信息
        player_names = request.form.getlist('player_names[]')
        player_roles = request.form.getlist('player_roles[]')
        
        # 更新队员信息（这里需要你的Player模型）
        # team.update_players(player_names, player_roles)

        db_session.commit()
        flash('战队信息更新成功', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('edit_team.html', team=team)

@main_bp.route('/manage_players/<int:team_id>', methods=['GET', 'POST'])
def manage_players(team_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    team = db_session.query(Team).filter_by(id=team_id).first()

    if not team or team.captain_id != session['user_id']:
        flash('您没有权限管理这支队伍', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            # 获取表单数据
            player_names = request.form.getlist('player_names[]')
            player_roles = request.form.getlist('player_roles[]')

            # ���证队员数量
            if len(player_names) > 5:
                flash('队伍最多只能有5名队员', 'danger')
                return redirect(url_for('main.manage_players', team_id=team_id))

            if len(player_names) == 0:
                flash('请至少添加一名队员', 'danger')
                return redirect(url_for('main.manage_players', team_id=team_id))

            # 删除现有队员
            db_session.query(Player).filter_by(team_id=team_id).delete()

            # 添加新队员
            for name, role in zip(player_names, player_roles):
                if name.strip() and role:  # 确保名字和角色都不为空
                    new_player = Player(
                        name=name.strip(),
                        role=role,
                        team_id=team_id
                    )
                    db_session.add(new_player)

            db_session.commit()
            flash('队员信息更新成功', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db_session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
            return redirect(url_for('main.manage_players', team_id=team_id))

    return render_template('manage_players.html', team=team)

@main_bp.route('/create_team', methods=['GET', 'POST'])
def create_team():
    if 'user_id' not in session or session.get('role') != 'participant':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        db_session = current_app.db_session
        name = request.form.get('name')
        country = request.form.get('country')
        
        # 检查战队名是否已存在
        if db_session.query(Team).filter_by(name=name).first():
            return jsonify({'success': False, 'error': '战队名已存在'})

        new_team = Team(
            name=name,
            country=country,
            captain_id=session['user_id']
        )

        # 处理头像上传
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                new_team.avatar_url = url_for('static', filename=f'uploads/team_avatars/{filename}')

        try:
            db_session.add(new_team)
            db_session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db_session.rollback()
            return jsonify({'success': False, 'error': str(e)})

    return render_template('create_team.html')

@main_bp.route('/tournament_info')
def tournament_info():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    tournaments = db_session.query(Tournament).all()
    return render_template('tournament_info.html', tournaments=tournaments)

@main_bp.route('/view_tournament/<int:tournament_id>')
def view_tournament(tournament_id):
    db_session = current_app.db_session
    tournament = db_session.query(Tournament).filter_by(id=tournament_id).first()
    
    if not tournament:
        flash('赛事不存在', 'danger')
        return redirect(url_for('main.tournament_list'))
    
    # 获取报名信息，但仅在用户有权限时显示
    registrations = []
    if session.get('user_id') and session.get('role') == 'manager':
        registrations = db_session.query(Registration).filter_by(tournament_id=tournament_id).all()
    
    return render_template('view_tournament.html', 
                         tournament=tournament, 
                         registrations=registrations)

@main_bp.route('/edit_registration/<int:registration_id>', methods=['GET', 'POST'])
def edit_registration(registration_id):
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    registration = db_session.query(Registration).filter_by(id=registration_id).first()

    if request.method == 'POST':
        registration.status = request.form.get('status', registration.status)

        db_session.commit()
        return redirect(url_for('main.view_tournament', tournament_id=registration.tournament.id))

    return render_template('edit_registration.html', registration=registration)

@main_bp.route('/add_tournament', methods=['POST'])
def add_tournament():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    name = request.form.get('name')
    location = request.form.get('location')
    start_time = request.form.get('start_time')
    status = request.form.get('status')
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
    if not name or not location or not start_time or not status:
        flash('所有字段都必须填写', 'error')
        return redirect(url_for('main.tournament_info'))

    new_tournament = Tournament(name=name, location=location, start_time=start_time, status=status)
    db_session.add(new_tournament)
    db_session.commit()

    flash('赛事信息已成功添加', 'success')
    return redirect(url_for('main.tournament_info'))

@main_bp.route('/delete_tournament/<int:tournament_id>')
def delete_tournament(tournament_id):
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    tournament = db_session.query(Tournament).filter_by(id=tournament_id).first()

    if not tournament:
        flash('赛事未找到', 'error')
        return redirect(url_for('main.tournament_info'))

    db_session.delete(tournament)
    db_session.commit()

    flash('赛事信息已成功删除', 'success')
    return redirect(url_for('main.tournament_info'))


@main_bp.route('/tournaments')
def tournament_list():
    db_session = current_app.db_session
    tournaments = db_session.query(Tournament).all()
    return render_template('tournament_list.html', tournaments=tournaments)


@main_bp.route('/tournament/<int:tournament_id>')
def tournament_detail(tournament_id):
    db_session = current_app.db_session
    tournament = db_session.query(Tournament).filter_by(id=tournament_id).first()
    if not tournament:
        flash('赛事不存在', 'danger')
        return redirect(url_for('main.tournament_list'))


    return render_template('tournament_detail.html', tournament=tournament)


@main_bp.route('/add_match/<int:tournament_id>', methods=['GET', 'POST'])
def add_match(tournament_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # 在函数开始就获取数据库会话
    db_session = current_app.db_session
    
    if request.method == 'POST':
        try:
            # 打印接收到的表单数据，用于调试
            print("Received form data:", request.form)
            
            team1_id = request.form.get('team1_id')
            team2_id = request.form.get('team2_id')
            tournament_format = request.form.get('tournament_format')
            match_time = request.form.get('match_time')
            
            # 验证数据
            if not all([team1_id, team2_id, tournament_format, match_time]):
                raise ValueError("所有字段都必须填写")
            
            # 创建新比赛 - 移除了 status 参数
            new_match = Match(
                tournament_id=tournament_id,
                team1_id=team1_id,
                team2_id=team2_id,
                tournament_format=tournament_format,
                match_time=datetime.strptime(match_time, '%Y-%m-%dT%H:%M')
            )
            
            db_session.add(new_match)
            db_session.flush()  # 获取新比赛的ID
            
            # 添加地图
            map_count = 1 if tournament_format == 'bo1' else (3 if tournament_format == 'bo3' else 5)
            for i in range(map_count):
                map_name = request.form.get(f'map_{i}')
                if map_name:
                    new_map = Map(
                        match_id=new_match.id,
                        name=map_name,
                        order=i+1
                    )
                    db_session.add(new_map)
            
            db_session.commit()
            return jsonify({
                'success': True,
                'redirect': url_for('main.view_tournament', tournament_id=tournament_id)
            })
            
        except Exception as e:
            db_session.rollback()
            print(f"Error adding match: {str(e)}")  # 打印错误信息
            import traceback
            traceback.print_exc()  # 打印完整的错误堆栈
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    # GET 请求处理
    teams = db_session.query(Team).all()
    return render_template('add_match.html', teams=teams, tournament_id=tournament_id)

@main_bp.route('/delete_match/<int:match_id>')
def delete_match(match_id):
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    match = db_session.query(Match).filter_by(id=match_id).first()

    if not match:
        flash('比赛未找到', 'error')
        return redirect(url_for('main.tournament_list'))

    tournament_id = match.tournament.id
    db_session.delete(match)
    db_session.commit()

    flash('比赛已成功删除', 'success')
    return redirect(url_for('main.view_tournament', tournament_id=tournament_id))

@main_bp.route('/statistics')
def statistics():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    
    # 获取统计数据
    total_teams = db_session.query(Team).count()
    total_players = db_session.query(Player).count()
    total_tournaments = db_session.query(Tournament).count()
    total_matches = db_session.query(Match).count()
    
    # 取最近的比赛统计
    recent_matches = db_session.query(Match).order_by(Match.match_time.desc()).limit(5).all()
    
    # 获取战队排名
    top_teams = db_session.query(Team, func.count(Match.winner_id).label('wins'))\
        .join(Match, Match.winner_id == Team.id)\
        .group_by(Team.id)\
        .order_by(desc('wins'))\
        .limit(10).all()

    return render_template('statistics.html',
                         total_teams=total_teams,
                         total_players=total_players,
                         total_tournaments=total_tournaments,
                         total_matches=total_matches,
                         recent_matches=recent_matches,
                         top_teams=top_teams)

@main_bp.route('/player_stats/<int:player_id>')
def player_stats(player_id):
    db_session = current_app.db_session
    player = db_session.query(Player).get_or_404(player_id)
    stats = db_session.query(Statistics).filter_by(player_id=player_id).all()
    return render_template('player_stats.html', player=player, stats=stats)

@main_bp.route('/team_stats/<int:team_id>')
def team_stats(team_id):
    db_session = current_app.db_session
    team = db_session.query(Team).get_or_404(team_id)
    matches = db_session.query(Match)\
        .filter((Match.team1_id == team_id) | (Match.team2_id == team_id))\
        .order_by(Match.match_time.desc())\
        .all()
    return render_template('team_stats.html', team=team, matches=matches)

@main_bp.route('/user_management')
def user_management():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    
    db_session = current_app.db_session
    users = db_session.query(User).all()
    return render_template('user_management.html', users=users)

@main_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    
    db_session = current_app.db_session
    user = db_session.query(User).filter_by(id=user_id).first()
    
    if not user:
        abort(404)  # 如果用户不存在，返回404错误
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        
        # 检查用户名和邮箱是否已被其他用户使用
        if db_session.query(User).filter(User.username == username, User.id != user_id).first():
            flash('用户名已被使用', 'error')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        if db_session.query(User).filter(User.email == email, User.id != user_id).first():
            flash('邮箱已被使用', 'error')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        user.username = username
        user.email = email
        user.role = role
        
        db_session.commit()
        flash('用户信息更新成功', 'success')
        return redirect(url_for('main.user_management'))
    
    return render_template('edit_user.html', user=user)

@main_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    
    if user_id == session['user_id']:
        flash('不能删除自己的账号', 'error')
        return redirect(url_for('main.user_management'))
    
    db_session = current_app.db_session
    user = db_session.query(User).filter_by(id=user_id).first()
    
    if not user:
        abort(404)  # 如果用户不存在，返回404错误
    
    # 检查用户是否是战队队长
    team = db_session.query(Team).filter_by(captain_id=user_id).first()
    if team:
        flash('该用户是战队队长，无法删除', 'error')
        return redirect(url_for('main.user_management'))
    
    db_session.delete(user)
    db_session.commit()
    flash('用户删除成功', 'success')
    return redirect(url_for('main.user_management'))

@main_bp.route('/tournament/<int:tournament_id>/register', methods=['POST'])
def tournament_register(tournament_id):
    if 'user_id' not in session or session.get('role') != 'participant':
        return jsonify({'success': False, 'error': '请先登录或确认您是参赛者身份'})

    db_session = current_app.db_session
    try:
        # 检查赛事是否存在
        tournament = db_session.query(Tournament).filter_by(id=tournament_id).first()
        if not tournament:
            return jsonify({'success': False, 'error': '赛事不存在'})
        
        # 检查赛事是否开放报名
        if tournament.status != 'registration_open':
            return jsonify({'success': False, 'error': '该赛事当前不接受报名'})
        
        # 获取用户的战队
        team = db_session.query(Team).filter_by(captain_id=session['user_id']).first()
        if not team:
            return jsonify({'success': False, 'error': '您还没有创建战队，请先创建战队'})
        
        # 检查用户是否已经报名
        existing_registration = db_session.query(Registration).filter_by(
            tournament_id=tournament_id,
            team_id=team.id
        ).first()
        
        if existing_registration:
            return jsonify({'success': False, 'error': '您的战队已经报名过该赛事'})
            
        # 创建新的报名记录
        new_registration = Registration(
            tournament_id=tournament_id,
            team_id=team.id,
            status='pending'  # 初始状态为待审核
        )
        
        db_session.add(new_registration)
        db_session.commit()
        
        return jsonify({'success': True, 'message': '报名成功，请等待审核'})
        
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/edit_match/<int:match_id>', methods=['GET', 'POST'])
def edit_match(match_id):
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

    db_session = current_app.db_session
    match = db_session.query(Match).filter_by(id=match_id).first()
    if not match:
        abort(404)  # 如果没有找到比赛，返回404错误
    
    if request.method == 'POST':
        try:
            match.team1_id = request.form.get('team1_id')
            match.team2_id = request.form.get('team2_id')
            match.tournament_format = request.form.get('tournament_format')
            match.match_time = datetime.strptime(request.form.get('match_time'), '%Y-%m-%dT%H:%M')
            
            # 处理地图信息
            map_count = {'bo1': 1, 'bo3': 3, 'bo5': 5}[match.tournament_format]
            
            # 删除现有的地图
            for map_obj in match.maps:
                db_session.delete(map_obj)
            
            # 添加新的地图
            for i in range(map_count):
                map_name = request.form.get(f'map_{i}')
                if map_name:
                    new_map = Map(
                        match_id=match.id,
                        name=map_name
                    )
                    db_session.add(new_map)
            
            db_session.commit()
            flash('比赛信息更新成功', 'success')
            return redirect(url_for('main.view_tournament', tournament_id=match.tournament_id))
            
        except Exception as e:
            db_session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
            return redirect(url_for('main.edit_match', match_id=match_id))

    teams = db_session.query(Team).all()
    return render_template('edit_match.html', match=match, teams=teams)