from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.utils import secure_filename
import os
import uuid
import imghdr
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import db, User, Post, Comment, bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# Initialize CSRF protection
csrf = CSRFProtect(app)

# Secure session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript from reading cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Provides some CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session timeout in seconds (1 hour)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['AVATAR_FOLDER'] = 'static/avatars'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB лимит
app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['jpeg', 'jpg', 'png', 'gif']
app.config['ALLOWED_VIDEO_EXTENSIONS'] = ['mp4', 'mov', 'avi', 'webm']

# Создаем директории для загрузок, если они не существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AVATAR_FOLDER'], exist_ok=True)

# Инициализируем базу данных с нашим приложением
db.init_app(app)
bcrypt.init_app(app)

# Настройка логирования
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/blog.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Запуск блога')

# Функция проверки, авторизован ли пользователь
def is_authenticated():
    return 'user_id' in session


# Декоратор для маршрутов, требующих аутентификации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Пожалуйста, войдите для доступа к этой странице.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Проверка допустимых расширений файлов
def allowed_file(filename):
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if extension in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        # Дополнительная проверка содержимого для изображений
        return 'image'
    elif extension in app.config['ALLOWED_VIDEO_EXTENSIONS']:
        return 'video'

    return None


# Функция для проверки MIME-типа загруженного файла
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return format


# Добавляем защитные заголовки для каждого ответа
@app.after_request
def add_security_headers(response):
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' https://cdnjs.cloudflare.com; connect-src 'self';"
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Enable XSS protection in browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# Обработчик главной страницы (требует аутентификации)
@app.route('/')
@login_required
def index():
    # Fetch posts with comments ordered by creation date
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if is_authenticated():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Проверки данных
        if not username or not email or not password or not confirm_password:
            flash('Все поля обязательны для заполнения.', 'error')
        elif password != confirm_password:
            flash('Пароли не совпадают.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Данное имя пользователя уже занято.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Данный email уже используется.', 'error')
        else:
            # Создаем нового пользователя
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if is_authenticated():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вы успешно вошли!', 'success')
            app.logger.info(f'Успешный вход: {username}')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')
            app.logger.warning(f'Неудачная попытка входа: {username} с IP {request.remote_addr}')

    return render_template('login.html')


# Выход из системы
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))


# Создание нового поста
@app.route('/post/create', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash('Заголовок и содержание поста обязательны.', 'error')
        return redirect(url_for('index'))

    # Проверяем, есть ли файл в запросе
    media_file = request.files.get('media')
    media_filename = None
    media_type = None

    if media_file and media_file.filename:
        file_type = allowed_file(media_file.filename)

        if not file_type:
            flash(
                'Недопустимый формат файла. Разрешены только изображения (JPEG, PNG, GIF) и видео (MP4, MOV, AVI, WEBM).',
                'error')
            return redirect(url_for('index'))

        # Дополнительная проверка для изображений
        if file_type == 'image':
            image_format = validate_image(media_file.stream)
            if not image_format or image_format not in app.config['ALLOWED_IMAGE_EXTENSIONS']:
                flash('Недопустимый формат изображения или поврежденный файл.', 'error')
                return redirect(url_for('index'))

        # Генерируем уникальное имя файла
        filename = str(uuid.uuid4()) + '.' + media_file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            media_file.save(filepath)
            media_filename = filename
            media_type = file_type
        except Exception as e:
            flash(f'Ошибка при загрузке файла: {str(e)}', 'error')
            return redirect(url_for('index'))

    # Создаем новый пост
    post = Post(
        title=title,
        content=content,
        media_file=media_filename,
        media_type=media_type,
        user_id=session['user_id']
    )

    db.session.add(post)
    db.session.commit()

    flash('Пост успешно создан!', 'success')
    return redirect(url_for('index'))


# Профиль пользователя
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    # Fetch user's posts with comments ordered by creation date
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    return render_template('profile.html', user=user, posts=posts)


# Редактирование профиля пользователя
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_username = request.form.get('username')
        email = request.form.get('email')

        # Проверки данных
        if not new_username or not email:
            flash('Имя пользователя и email обязательны.', 'error')
        elif new_username != user.username and User.query.filter_by(username=new_username).first():
             flash('Данное имя пользователя уже занято.', 'error')
        else:
            user.username = new_username
            user.email = email
            
            # Обработка загрузки аватара
            avatar_file = request.files.get('avatar')
            if avatar_file and avatar_file.filename:
                file_ext = avatar_file.filename.rsplit('.', 1)[1].lower() if '.' in avatar_file.filename else ''
                
                if file_ext not in app.config['ALLOWED_IMAGE_EXTENSIONS']:
                    flash('Недопустимый формат файла для аватара. Разрешены только изображения (JPEG, PNG, GIF).', 'error')
                else:
                    # Удаляем старый аватар, если он существует
                    if user.avatar and os.path.exists(os.path.join(app.config['AVATAR_FOLDER'], user.avatar)):
                        try:
                            os.remove(os.path.join(app.config['AVATAR_FOLDER'], user.avatar))
                        except Exception as e:
                            print(f"Ошибка при удалении старого аватара: {str(e)}")
                    
                    # Генерируем уникальное имя файла
                    avatar_filename = f"avatar_{user_id}_{str(uuid.uuid4())}.{file_ext}"
                    avatar_path = os.path.join(app.config['AVATAR_FOLDER'], avatar_filename)
                    
                    try:
                        avatar_file.save(avatar_path)
                        user.avatar = avatar_filename
                    except Exception as e:
                        flash(f'Ошибка при загрузке аватара: {str(e)}', 'error')
            
            db.session.commit()
            session['username'] = user.username # Update username in session
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile', user_id=user.id))

    return render_template('edit_profile.html', user=user)


# Изменение пароля
@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        # Проверки данных
        if not old_password or not new_password or not confirm_new_password:
            flash('Все поля обязательны для заполнения.', 'error')
        elif not user.check_password(old_password):
            flash('Неверный старый пароль.', 'error')
        elif new_password != confirm_new_password:
            flash('Новые пароли не совпадают.', 'error')
        else:
            user.set_password(new_password)
            db.session.commit()
            flash('Пароль успешно изменен!', 'success')
            return redirect(url_for('profile', user_id=user.id))

    return render_template('change_password.html')


# Создание нового комментария к посту
@app.route('/comment/create/<int:post_id>', methods=['POST'])
@login_required
def create_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('Содержание комментария обязательно.', 'error')
        return redirect(url_for('index'))
    
    comment = Comment(
        content=content,
        user_id=session['user_id'],
        post_id=post_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Комментарий успешно добавлен!', 'success')
    return redirect(url_for('index'))


# Удаление комментария
@app.route('/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Проверяем, что пользователь является автором комментария или автором поста или администратором
    user_id = session['user_id']
    post = Post.query.get(comment.post_id)
    
    if comment.user_id != user_id and post.user_id != user_id and user_id != 1:
        flash('У вас нет прав для удаления этого комментария.', 'error')
        return redirect(url_for('index'))
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Комментарий успешно удален!', 'success')
    return redirect(url_for('index'))


# Удаление поста
@app.route('/post/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Проверяем, что пользователь является автором поста или администратором
    user_id = session['user_id']
    
    if post.user_id != user_id and user_id != 1:
        flash('У вас нет прав для удаления этого поста.', 'error')
        return redirect(url_for('index'))
    
    # Если есть медиа-файл, удаляем его
    if post.media_file and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], post.media_file)):
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.media_file))
        except Exception as e:
            print(f"Ошибка при удалении медиа-файла: {str(e)}")
    
    # Удаляем пост (комментарии удалятся автоматически благодаря cascade)
    db.session.delete(post)
    db.session.commit()
    
    flash('Пост успешно удален!', 'success')
    
    # Если удаление было выполнено из профиля, возвращаемся в профиль
    if request.referrer and 'profile' in request.referrer:
        return redirect(url_for('profile', user_id=user_id))
    
    return redirect(url_for('index'))


# Обработчик ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# Обработчик ошибки 413 (слишком большой файл)
@app.errorhandler(413)
def request_entity_too_large(e):
    flash('Размер файла превышает допустимый лимит (100 МБ).', 'error')
    return redirect(url_for('index'))


# Обработчик ошибки 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.context_processor
def inject_is_admin():
    def is_admin():
        if 'user_id' not in session:
            return False
        return session.get('user_id') == 1  # ID 1 - это админ

    return dict(is_admin=is_admin)


# Регистрируем блюпринт для админ-панели
from admin import admin_bp
app.register_blueprint(admin_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы в БД при запуске
    app.run(debug=True)