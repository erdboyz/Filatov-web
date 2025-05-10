from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory, Response, jsonify
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
import json
from flask_mail import Mail, Message
from datetime import datetime
import time
import traceback

from models import db, User, Post, Comment, bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24)
# Initialize CSRF protection
csrf = CSRFProtect(app)

# Secure session configuration
app.config['SESSION_COOKIE_SECURE'] = True  # Set to True in production with HTTPS
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

# Настройка Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or 'your-yandex-email@ya.ru'
# For Yandex personal accounts, create an app password in the account security settings
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or 'your-yandex-email@ya.ru'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or 'your-app-password'
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['MAIL_DEBUG'] = True  # Enable mail debug

# Создаем директории для загрузок, если они не существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AVATAR_FOLDER'], exist_ok=True)

# Инициализируем базу данных с нашим приложением
db.init_app(app)
bcrypt.init_app(app)
mail = Mail(app)

# Enhanced logging setup
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure main application logger
class RequestFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'request_id'):
            record.request_id = record.request_id
        else:
            record.request_id = '-'
            
        if hasattr(record, 'user_id'):
            record.user_id = record.user_id
        else:
            record.user_id = '-'
            
        if hasattr(record, 'ip'):
            record.ip = record.ip
        else:
            record.ip = '-'
            
        return super().format(record)

# Main application log
app_formatter = RequestFormatter(
    '%(asctime)s [%(request_id)s] [%(levelname)s] [user:%(user_id)s] [ip:%(ip)s]: %(message)s [in %(pathname)s:%(lineno)d]'
)
file_handler = RotatingFileHandler('logs/blog.log', maxBytes=10485760, backupCount=20, encoding='utf-8')
file_handler.setFormatter(app_formatter)
file_handler.setLevel(logging.INFO)

# Security log for authentication and security-related events
security_formatter = RequestFormatter(
    '%(asctime)s [%(request_id)s] [%(levelname)s] [user:%(user_id)s] [ip:%(ip)s]: %(message)s'
)
security_handler = RotatingFileHandler('logs/security.log', maxBytes=10485760, backupCount=20, encoding='utf-8')
security_handler.setFormatter(security_formatter)
security_handler.setLevel(logging.INFO)

# Access log for HTTP requests
access_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s]: %(message)s'
)
access_handler = RotatingFileHandler('logs/access.log', maxBytes=10485760, backupCount=20, encoding='utf-8')
access_handler.setFormatter(access_formatter)
access_handler.setLevel(logging.INFO)

# Error log specifically for errors
error_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s]: %(message)s\n%(exc_info)s'
)
error_handler = RotatingFileHandler('logs/error.log', maxBytes=10485760, backupCount=20, encoding='utf-8')
error_handler.setFormatter(error_formatter)
error_handler.setLevel(logging.ERROR)

# Create and configure loggers
app.logger.addHandler(file_handler)
app.logger.addHandler(error_handler)
app.logger.setLevel(logging.INFO)

# Create security logger
security_logger = logging.getLogger('security')
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)
security_logger.propagate = False

# Create access logger
access_logger = logging.getLogger('access')
access_logger.addHandler(access_handler)
access_logger.setLevel(logging.INFO)
access_logger.propagate = False

app.logger.info('Запуск блога')

# Log all requests
@app.before_request
def log_request_info():
    # Generate a unique request ID
    request_id = str(uuid.uuid4())[:8]
    request.request_id = request_id
    
    # Get user ID if authenticated
    user_id = session.get('user_id', '-')
    
    # Get client IP
    ip = request.remote_addr
    
    # Log the request
    access_logger.info(
        f'Request: {request.method} {request.path} [request_id:{request_id}] [user:{user_id}] [ip:{ip}]'
    )
    
    # Set start time to calculate response time
    request.start_time = time.time()

@app.after_request
def log_response_info(response):
    # Calculate response time
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
    else:
        duration = 0
    
    # Get request ID
    request_id = getattr(request, 'request_id', '-')
    
    # Get user ID if authenticated
    user_id = session.get('user_id', '-')
    
    # Get client IP
    ip = request.remote_addr
    
    # Log the response
    access_logger.info(
        f'Response: {request.method} {request.path} {response.status_code} [{duration:.4f}s] [request_id:{request_id}] [user:{user_id}] [ip:{ip}]'
    )
    
    return response

# Enhanced error logging
@app.errorhandler(Exception)
def handle_exception(e):
    # Get request ID
    request_id = getattr(request, 'request_id', '-')
    
    # Get user ID if authenticated
    user_id = session.get('user_id', '-')
    
    # Get client IP
    ip = request.remote_addr
    
    # Log the error with traceback
    app.logger.error(
        f'Unhandled exception: {str(e)} [request_id:{request_id}] [user:{user_id}] [ip:{ip}]',
        exc_info=True
    )
    
    # Return an appropriate response
    return render_template('error.html', error=str(e)), 500

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
    # Get the page parameter from the request query string, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of posts per page
    
    # Fetch posts with pagination
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    
    return render_template('index.html', posts=posts, pagination=pagination)


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
        
        # Get request info for logging
        request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')

        # Проверки данных
        if not username or not email or not password or not confirm_password:
            flash('Все поля обязательны для заполнения.', 'error')
            security_logger.warning(
                f'Неудачная попытка регистрации: неполные данные формы',
                extra={
                    'request_id': request_id,
                    'user_id': '-',
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
        elif password != confirm_password:
            flash('Пароли не совпадают.', 'error')
            security_logger.warning(
                f'Неудачная попытка регистрации: несовпадение паролей',
                extra={
                    'request_id': request_id,
                    'user_id': '-', 
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
        elif User.query.filter_by(username=username).first():
            flash('Данное имя пользователя уже занято.', 'error')
            security_logger.warning(
                f'Неудачная попытка регистрации: имя пользователя занято - {username}',
                extra={
                    'request_id': request_id,
                    'user_id': '-',
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
        elif User.query.filter_by(email=email).first():
            flash('Данный email уже используется.', 'error')
            security_logger.warning(
                f'Неудачная попытка регистрации: email занят - {email}',
                extra={
                    'request_id': request_id,
                    'user_id': '-',
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
        else:
            # Создаем нового пользователя (неподтвержденного)
            user = User(username=username, email=email, is_verified=False)
            user.set_password(password)
            
            # Генерируем код подтверждения
            verification_code = user.generate_verification_code()
            
            db.session.add(user)
            db.session.commit()
            
            # Log successful registration
            security_logger.info(
                f'Новый пользователь зарегистрирован (неподтвержденный): {username}, {email}',
                extra={
                    'request_id': request_id,
                    'user_id': user.id,
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
            
            # Отправляем письмо с кодом подтверждения
            try:
                msg = Message(
                    'Подтверждение регистрации',
                    recipients=[email],
                    charset='utf-8'
                )
                
                verification_message = (
                    "Для подтверждения регистрации, пожалуйста, введите следующий код:\n\n"
                    f"{verification_code}\n\n"
                    "Код действителен в течение 30 минут.\n\n"
                    "Если вы не регистрировались на нашем сайте, проигнорируйте это письмо."
                )
                
                msg.body = verification_message
                mail.send(msg)
                
                # Сохраняем ID пользователя в сессии для проверки электронной почты
                session['verifying_user_id'] = user.id
                
                app.logger.info(f'Код подтверждения отправлен: {email}')
                flash('На вашу почту отправлен код подтверждения. Введите его для завершения регистрации.', 'info')
                return redirect(url_for('verify_email'))
            except Exception as e:
                # В случае ошибки отправки удаляем пользователя и отображаем сообщение об ошибке
                db.session.delete(user)
                db.session.commit()
                
                error_msg = f'Ошибка отправки письма: {str(e)}'
                app.logger.error(error_msg, exc_info=True)
                security_logger.error(
                    f'Регистрация отменена из-за ошибки отправки письма: {str(e)}',
                    extra={
                        'request_id': request_id,
                        'user_id': '-',
                        'ip': ip,
                        'user_agent': user_agent
                    }
                )
                
                flash(f'Произошла ошибка при отправке письма подтверждения: {str(e)}. Пожалуйста, попробуйте еще раз.', 'error')

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
        
        # Get request info for logging
        request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Проверяем, подтвержден ли аккаунт
            if not user.is_verified:
                # Сохраняем ID пользователя в сессии для проверки электронной почты
                session['verifying_user_id'] = user.id
                security_logger.warning(
                    f'Попытка входа в неподтвержденный аккаунт: {username}',
                    extra={
                        'request_id': request_id,
                        'user_id': user.id,
                        'ip': ip
                    }
                )
                flash('Ваш аккаунт еще не подтвержден. Пожалуйста, подтвердите вашу электронную почту.', 'warning')
                return redirect(url_for('verify_email'))
                
            session['user_id'] = user.id
            session['username'] = user.username
            if user.nickname:
                session['nickname'] = user.nickname
                
            # Log successful login with security logger
            security_logger.info(
                f'Успешный вход: {username}',
                extra={
                    'request_id': request_id,
                    'user_id': user.id,
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            # Log failed login attempt with security logger
            security_logger.warning(
                f'Неудачная попытка входа: {username}',
                extra={
                    'request_id': request_id,
                    'user_id': '-',
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
            flash('Неверное имя пользователя или пароль.', 'error')

    return render_template('login.html')


# Выход из системы
@app.route('/logout')
def logout():
    # Get user info before clearing the session
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Get request info for logging
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    ip = request.remote_addr
    
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('nickname', None)
    
    # Log logout with security logger if user was logged in
    if user_id:
        security_logger.info(
            f'Пользователь вышел из системы: {username}',
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'ip': ip
            }
        )
    
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))


# Создание нового поста
@app.route('/post/create', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    # Расширенная валидация
    errors = []
    
    if not title:
        errors.append('Заголовок поста обязателен')
    elif len(title) > 100:
        errors.append('Заголовок поста не должен превышать 100 символов')
        
    if not content:
        errors.append('Содержание поста обязательно')
    elif len(content) > 5000:
        errors.append('Содержание поста слишком длинное (максимум 5000 символов)')

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('index'))

    try:
        # Создаем новый пост
        post = Post(
            title=title,
            content=content,
            user_id=session['user_id']
        )
        
        db.session.add(post)
        db.session.commit()

        # Обработка медиа файлов
        media_files = request.files.getlist('media[]')
        MAX_FILES = 5
        
        # Ограничиваем количество файлов до MAX_FILES
        if len(media_files) > MAX_FILES:
            flash(f'Превышен лимит файлов. Максимальное количество файлов: {MAX_FILES}.', 'error')
            media_files = media_files[:MAX_FILES]
        
        processed_files = []
        
        for media_file in media_files:
            if media_file and media_file.filename:
                try:
                    # Проверка размера файла
                    file_content = media_file.read()
                    media_file.seek(0)  # Сброс указателя после чтения
                    
                    # Максимальный размер 100 МБ
                    max_size = 100 * 1024 * 1024
                    if len(file_content) > max_size:
                        flash(f'Файл {media_file.filename} превышает допустимый лимит в 100 МБ.', 'error')
                        continue
                    
                    file_type = allowed_file(media_file.filename)
                    
                    if not file_type:
                        flash(
                            f'Файл {media_file.filename}: Недопустимый формат файла. Разрешены только изображения (JPEG, PNG, GIF) и видео (MP4, MOV, AVI, WEBM).',
                            'error')
                        continue

                    # Дополнительная проверка для изображений
                    if file_type == 'image':
                        image_format = validate_image(media_file.stream)
                        if not image_format or image_format not in app.config['ALLOWED_IMAGE_EXTENSIONS']:
                            flash(f'Файл {media_file.filename}: Недопустимый формат изображения или поврежденный файл.', 'error')
                            continue

                    # Генерируем уникальное имя файла
                    original_filename = secure_filename(media_file.filename)
                    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                    filename = str(uuid.uuid4()) + '.' + file_ext
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    media_file.save(filepath)
                    
                    # Добавляем информацию о файле в список
                    processed_files.append({
                        'filename': filename,
                        'type': file_type,
                        'original_name': original_filename
                    })
                    
                except Exception as e:
                    app.logger.error(f'Ошибка при загрузке файла {media_file.filename}: {str(e)}')
                    flash(f'Ошибка при загрузке файла {media_file.filename}. Пожалуйста, попробуйте еще раз.', 'error')
        
        # Обновляем пост с информацией о медиа файлах
        if processed_files:
            post.media_files = json.dumps(processed_files)
            db.session.commit()

        flash('Пост успешно создан!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при создании поста: {str(e)}')
        flash('Произошла ошибка при создании поста. Пожалуйста, попробуйте еще раз.', 'error')
        return redirect(url_for('index'))


# Профиль пользователя
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get the page parameter from the request query string, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of posts per page
    
    # Fetch user's posts with pagination
    pagination = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    
    return render_template('profile.html', user=user, posts=posts, pagination=pagination)


# Страница настроек аккаунта
@app.route('/account/settings', methods=['GET'])
@login_required
def account_settings():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    return render_template('account_settings.html', user=user)


# Обновление профиля пользователя
@app.route('/account/update/profile', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_username = request.form.get('username')
        nickname = request.form.get('nickname', '').strip() or None
        email = request.form.get('email')
        remove_avatar = request.form.get('remove_avatar') == '1'

        # Проверки данных
        if not new_username or not email:
            flash('Имя пользователя и email обязательны.', 'error')
        elif new_username != user.username and User.query.filter_by(username=new_username).first():
             flash('Данное имя пользователя уже занято.', 'error')
        else:
            user.username = new_username
            user.email = email
            user.nickname = nickname
            
            # Обработка удаления аватара
            if remove_avatar and user.avatar:
                # Удаляем файл аватара
                avatar_path = os.path.join(app.config['AVATAR_FOLDER'], user.avatar)
                if os.path.exists(avatar_path):
                    try:
                        os.remove(avatar_path)
                    except Exception as e:
                        app.logger.error(f"Ошибка при удалении аватара: {str(e)}")
                
                # Удаляем ссылку на аватар из базы данных
                user.avatar = None
            # Обработка загрузки нового аватара
            elif not remove_avatar:
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
                                app.logger.error(f"Ошибка при удалении старого аватара: {str(e)}")
                        
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
            if nickname:
                session['nickname'] = nickname
            else:
                session.pop('nickname', None)  # Remove nickname if it was unset
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('account_settings', _anchor='profile'))

    return redirect(url_for('account_settings', _anchor='profile'))


# Обновление пароля
@app.route('/account/update/password', methods=['POST'])
@login_required
def update_password():
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
        
    return redirect(url_for('account_settings', _anchor='password'))


# Обновление настроек приватности
@app.route('/account/update/privacy', methods=['POST'])
@login_required
def update_privacy():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        hide_email = 'hide_email' in request.form
        hide_posts = 'hide_posts' in request.form

        user.hide_email = hide_email
        user.hide_posts = hide_posts
        
        db.session.commit()
        flash('Настройки приватности успешно обновлены!', 'success')
    
    return redirect(url_for('account_settings', _anchor='privacy'))


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
    
    # Если есть медиа-файлы, удаляем их
    media_files = post.get_media_files()
    if media_files:
        for media in media_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], media.get('filename', ''))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    app.logger.error(f"Ошибка при удалении медиа-файла {media.get('filename', '')}: {str(e)}")
    
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
    # Get request info for logging
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    ip = request.remote_addr
    user_id = session.get('user_id', '-')
    path = request.path
    
    app.logger.warning(
        f'404 ошибка: {path}',
        extra={
            'request_id': request_id,
            'user_id': user_id,
            'ip': ip
        }
    )
    return render_template('404.html'), 404


# Обработчик ошибки 413 (слишком большой файл)
@app.errorhandler(413)
def request_entity_too_large(e):
    # Get request info for logging
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    ip = request.remote_addr
    user_id = session.get('user_id', '-')
    path = request.path
    
    app.logger.warning(
        f'413 ошибка (превышен размер файла): {path}',
        extra={
            'request_id': request_id,
            'user_id': user_id,
            'ip': ip
        }
    )
    flash('Размер файла превышает допустимый лимит (100 МБ).', 'error')
    return redirect(url_for('index'))


# Обработчик ошибки 500
@app.errorhandler(500)
def internal_server_error(e):
    # Get request info for logging
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    ip = request.remote_addr
    user_id = session.get('user_id', '-')
    path = request.path
    
    app.logger.error(
        f'500 ошибка: {path}, {str(e)}',
        extra={
            'request_id': request_id,
            'user_id': user_id,
            'ip': ip
        },
        exc_info=True
    )
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


@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    # Get request info for logging
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Проверяем, есть ли в сессии ID пользователя для подтверждения
    verifying_user_id = session.get('verifying_user_id')
    if not verifying_user_id:
        security_logger.warning(
            'Попытка подтверждения с истекшей/недействительной сессией',
            extra={
                'request_id': request_id,
                'user_id': '-',
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash('Сессия подтверждения истекла или недействительна.', 'error')
        return redirect(url_for('register'))
    
    # Находим пользователя
    user = User.query.get(verifying_user_id)
    if not user:
        security_logger.warning(
            f'Попытка подтверждения для несуществующего пользователя ID: {verifying_user_id}',
            extra={
                'request_id': request_id,
                'user_id': verifying_user_id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('register'))
    
    # Проверяем, не подтвержден ли уже пользователь
    if user.is_verified:
        session.pop('verifying_user_id', None)
        security_logger.info(
            f'Попытка повторного подтверждения уже подтвержденного аккаунта: {user.username}',
            extra={
                'request_id': request_id,
                'user_id': user.id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash('Ваш аккаунт уже подтвержден. Пожалуйста, войдите.', 'info')
        return redirect(url_for('login'))
    
    # Проверяем, не истек ли срок действия кода
    if not user.verification_expires_at or user.verification_expires_at < datetime.utcnow():
        # Если срок истек, генерируем новый код и отправляем его
        verification_code = user.generate_verification_code()
        db.session.commit()
        
        security_logger.info(
            f'Сгенерирован новый код подтверждения из-за истечения срока: {user.username}',
            extra={
                'request_id': request_id,
                'user_id': user.id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        
        try:
            msg = Message(
                'Новый код подтверждения регистрации',
                recipients=[user.email],
                charset='utf-8'
            )
            
            verification_message = (
                "Ваш предыдущий код истек. Вот новый код подтверждения:\n\n"
                f"{verification_code}\n\n"
                "Код действителен в течение 30 минут.\n\n"
                "Если вы не регистрировались на нашем сайте, проигнорируйте это письмо."
            )
            
            msg.body = verification_message
            mail.send(msg)
            flash('Срок действия предыдущего кода истек. Новый код отправлен на вашу почту.', 'info')
        except Exception as e:
            error_msg = f'Ошибка отправки письма: {str(e)}'
            app.logger.error(error_msg, exc_info=True)
            security_logger.error(
                f'Ошибка отправки нового кода подтверждения: {user.username}, {str(e)}',
                extra={
                    'request_id': request_id,
                    'user_id': user.id,
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
            flash(f'Произошла ошибка при отправке нового кода: {str(e)}. Пожалуйста, попробуйте еще раз.', 'error')
            return redirect(url_for('register'))
    
    # Обработка запроса на подтверждение
    if request.method == 'POST':
        code = request.form.get('verification_code')
        
        if not code:
            flash('Пожалуйста, введите код подтверждения.', 'error')
            security_logger.warning(
                f'Пустой код подтверждения: {user.username}',
                extra={
                    'request_id': request_id,
                    'user_id': user.id,
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
        elif code != user.verification_code:
            flash('Неверный код подтверждения. Пожалуйста, проверьте и попробуйте снова.', 'error')
            security_logger.warning(
                f'Неверный код подтверждения: {user.username}',
                extra={
                    'request_id': request_id,
                    'user_id': user.id,
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
        else:
            # Код верный, подтверждаем пользователя
            user.is_verified = True
            user.verification_code = None  # Очищаем код
            user.verification_expires_at = None
            db.session.commit()
            
            # Удаляем данные подтверждения из сессии
            session.pop('verifying_user_id', None)
            
            security_logger.info(
                f'Успешное подтверждение аккаунта: {user.username}',
                extra={
                    'request_id': request_id,
                    'user_id': user.id,
                    'ip': ip,
                    'user_agent': user_agent
                }
            )
            
            flash('Регистрация успешно подтверждена! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
    
    return render_template('verify_email.html')


@app.route('/resend-verification', methods=['GET'])
def resend_verification():
    # Get request info for logging
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Проверяем, есть ли в сессии ID пользователя для подтверждения
    verifying_user_id = session.get('verifying_user_id')
    if not verifying_user_id:
        security_logger.warning(
            'Попытка повторной отправки кода с истекшей/недействительной сессией',
            extra={
                'request_id': request_id,
                'user_id': '-',
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash('Сессия подтверждения истекла или недействительна.', 'error')
        return redirect(url_for('register'))
    
    # Находим пользователя
    user = User.query.get(verifying_user_id)
    if not user:
        security_logger.warning(
            f'Попытка повторной отправки кода для несуществующего пользователя ID: {verifying_user_id}',
            extra={
                'request_id': request_id,
                'user_id': verifying_user_id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('register'))
    
    # Проверяем, не подтвержден ли уже пользователь
    if user.is_verified:
        session.pop('verifying_user_id', None)
        security_logger.info(
            f'Попытка повторной отправки кода для уже подтвержденного аккаунта: {user.username}',
            extra={
                'request_id': request_id,
                'user_id': user.id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash('Ваш аккаунт уже подтвержден. Пожалуйста, войдите.', 'info')
        return redirect(url_for('login'))
    
    # Генерируем новый код и отправляем его
    verification_code = user.generate_verification_code()
    db.session.commit()
    
    security_logger.info(
        f'Запрос на повторную отправку кода подтверждения: {user.username}',
        extra={
            'request_id': request_id,
            'user_id': user.id,
            'ip': ip,
            'user_agent': user_agent
        }
    )
    
    try:
        msg = Message(
            'Новый код подтверждения регистрации',
            recipients=[user.email],
            charset='utf-8'
        )
        
        verification_message = (
            "Вот новый код подтверждения:\n\n"
            f"{verification_code}\n\n"
            "Код действителен в течение 30 минут.\n\n"
            "Если вы не регистрировались на нашем сайте, проигнорируйте это письмо."
        )
        
        msg.body = verification_message
        mail.send(msg)
        
        security_logger.info(
            f'Новый код подтверждения успешно отправлен: {user.username}',
            extra={
                'request_id': request_id,
                'user_id': user.id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        
        flash('Новый код подтверждения отправлен на вашу почту.', 'info')
    except Exception as e:
        error_msg = f'Ошибка отправки письма: {str(e)}'
        app.logger.error(error_msg, exc_info=True)
        security_logger.error(
            f'Ошибка повторной отправки кода подтверждения: {user.username}, {str(e)}',
            extra={
                'request_id': request_id,
                'user_id': user.id,
                'ip': ip,
                'user_agent': user_agent
            }
        )
        flash(f'Произошла ошибка при отправке нового кода: {str(e)}. Пожалуйста, попробуйте еще раз.', 'error')
    
    return redirect(url_for('verify_email'))


# Редиректы для обратной совместимости со старыми URL
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        return update_profile()
    return redirect(url_for('account_settings', _anchor='profile'))


@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        return update_password()
    return redirect(url_for('account_settings', _anchor='password'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы в БД при запуске
    app.run(debug=False)