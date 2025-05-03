from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.utils import secure_filename
import os
import uuid
import imghdr

from models import db, User, Post

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB лимит
app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['jpeg', 'jpg', 'png', 'gif']
app.config['ALLOWED_VIDEO_EXTENSIONS'] = ['mp4', 'mov', 'avi', 'webm']

# Создаем директорию для загрузок, если она не существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Инициализируем базу данных с нашим приложением
db.init_app(app)


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
        return 'image'
    elif extension in app.config['ALLOWED_VIDEO_EXTENSIONS']:
        return 'video'

    return None


# Обработчик главной страницы (требует аутентификации)
@app.route('/')
@login_required
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')

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