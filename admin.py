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

    # Удаляем прикрепленный файл, если он есть
    if post.media_file:
        from flask import current_app
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], post.media_file))
        except (FileNotFoundError, OSError):
            pass  # Игнорируем ошибки, если файл не найден

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

    # Находим все посты пользователя и удаляем прикрепленные файлы
    from flask import current_app
    posts = Post.query.filter_by(user_id=user_id).all()
    for post in posts:
        if post.media_file:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], post.media_file))
            except (FileNotFoundError, OSError):
                pass

    # Удаляем пользователя (каскадное удаление всех его постов)
    db.session.delete(user)
    db.session.commit()

    flash(f'Пользователь "{user.username}" и все его посты были успешно удалены.', 'success')
    return redirect(url_for('admin.admin_panel'))