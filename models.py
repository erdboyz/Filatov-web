from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
import json
import secrets

# Инициализация SQLAlchemy без привязки к приложению
db = SQLAlchemy()
bcrypt = Bcrypt()

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    verification_expires_at = db.Column(db.DateTime, nullable=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    nickname = db.Column(db.String(80), nullable=True)
    hide_email = db.Column(db.Boolean, default=False)
    hide_posts = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
        
    def generate_verification_code(self):
        # Generate a 6-digit code
        self.verification_code = ''.join(secrets.choice('0123456789') for _ in range(6))
        # Set expiration time (30 minutes from now)
        self.verification_expires_at = datetime.utcnow() + timedelta(minutes=30)
        return self.verification_code


# Модель поста
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_files = db.Column(db.Text, nullable=True)  # JSON строка с информацией о файлах
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    # Метод для получения списка медиа-файлов
    def get_media_files(self):
        if not self.media_files:
            return []
        try:
            return json.loads(self.media_files)
        except:
            return []


# Модель комментария
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)