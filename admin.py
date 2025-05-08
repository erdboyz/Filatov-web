from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
import os
from models import db, User, Post
from functools import wraps

# Создаем Blueprint для административной панели
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# Функция проверки, авторизован ли пользователь (импортировать из app не можем)
def is_authenticated():
    return 'user_id' in session


# Декоратор для маршрутов, требующих аутентификации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Пожалуйста, войдите для доступа к этой странице.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Проверка, является ли пользователь администратором
def is_admin():
    if 'user_id' not in session:
        return False

    user = User.query.get(session['user_id'])
    # Здесь можно установить любой критерий для определения администратора
    # Например, первый зарегистрированный пользователь (ID = 1)
    return user and user.id == 1  # Пользователь с ID 1 считается администратором


# Декоратор для маршрутов, требующих административных прав
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Доступ запрещен. Необходимы права администратора.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# Маршрут для отображения административной панели
@admin_bp.route('/')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/panel.html', users=users, posts=posts)


# Маршрут для удаления поста
@admin_bp.route('/posts/delete/<int:post_id>', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Удаляем прикрепленные файлы, если они есть
    media_files = post.get_media_files()
    if media_files:
        from flask import current_app
        for media in media_files:
            filename = media.get('filename')
            if filename:
                try:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except (FileNotFoundError, OSError) as e:
                    current_app.logger.error(f"Ошибка при удалении файла {filename}: {str(e)}")

    # Удаляем запись из базы данных
    db.session.delete(post)
    db.session.commit()

    flash(f'Пост "{post.title}" был успешно удален.', 'success')
    return redirect(url_for('admin.admin_panel'))


# Маршрут для удаления пользователя
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Запрещаем удаление администратора (себя)
    if user_id == 1:
        flash('Невозможно удалить аккаунт администратора.', 'error')
        return redirect(url_for('admin.admin_panel'))

    user = User.query.get_or_404(user_id)

    # Находим все посты пользователя
    from flask import current_app
    posts = Post.query.filter_by(user_id=user_id).all()
    
    # Сначала удаляем каждый пост отдельно
    for post in posts:
        # Удаляем прикрепленные файлы
        media_files = post.get_media_files()
        if media_files:
            for media in media_files:
                filename = media.get('filename')
                if filename:
                    try:
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except (FileNotFoundError, OSError) as e:
                        current_app.logger.error(f"Ошибка при удалении файла {filename}: {str(e)}")
        
        # Удаляем сам пост из базы данных
        db.session.delete(post)
    
    # После удаления всех постов удаляем пользователя
    db.session.delete(user)
    
    try:
        db.session.commit()
        flash(f'Пользователь "{user.username}" и все его посты были успешно удалены.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении пользователя: {str(e)}")
        flash(f'Произошла ошибка при удалении пользователя. {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_panel'))