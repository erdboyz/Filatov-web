# Blog Application with Email Verification

A Flask-based blog application with user authentication, email verification, and admin functionality.

## English Instructions

### Local Development Setup

1. **Clone the repository**
   ```
   git clone [repository-url]
   cd Blog
   ```

2. **Create a virtual environment**
   ```
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

5. **Set up email credentials**
   
   Configure your email service by setting environment variables:
   - Windows:
     ```
     set MAIL_USERNAME=your-email@gmail.com
     set MAIL_PASSWORD=your-app-password
     set MAIL_DEFAULT_SENDER=your-email@gmail.com
     set SECRET_KEY=your-secret-key
     ```
   - macOS/Linux:
     ```
     export MAIL_USERNAME=your-email@gmail.com
     export MAIL_PASSWORD=your-app-password
     export MAIL_DEFAULT_SENDER=your-email@gmail.com
     export SECRET_KEY=your-secret-key
     ```

   For Gmail, you'll need to:
   - Enable 2-factor authentication
   - Create an App Password in your Google Account security settings

   Alternatively, edit `app.py` directly with your credentials (for development only, not recommended for production).

6. **Initialize the database**
   ```
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Run the application**
   ```
   python app.py
   ```

8. **Access the application**
   
   Open your browser and navigate to `http://127.0.0.1:5000`

### Production Deployment

1. **Update security settings**
   
   Edit `app.py` to enable secure cookies:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   ```

2. **Set environment variables on your server**
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   SECRET_KEY=your-secret-key
   ```

3. **Disable debug mode**
   
   Set `debug=False` in the `app.run()` call or use an environment variable.

4. **Use a production WSGI server**
   
   For deployment with Gunicorn (included in requirements.txt):
   ```
   gunicorn app:app
   ```

5. **Set up a reverse proxy**
   
   Configure Nginx or Apache to proxy requests to your Flask application.

6. **Set up SSL/TLS**
   
   Obtain and configure an SSL certificate for secure communication.

---

## Инструкции на русском языке

### Локальная настройка для разработки

1. **Клонировать репозиторий**
   ```
   git clone [url-репозитория]
   cd Blog
   ```

2. **Создать виртуальное окружение**
   ```
   python -m venv .venv
   ```

3. **Активировать виртуальное окружение**
   - Windows:
     ```
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source .venv/bin/activate
     ```

4. **Установить зависимости**
   ```
   pip install -r requirements.txt
   ```

5. **Настроить учетные данные электронной почты**
   
   Настройте ваш почтовый сервис, установив переменные окружения:
   - Windows:
     ```
     set MAIL_USERNAME=your-email@gmail.com
     set MAIL_PASSWORD=your-app-password
     set MAIL_DEFAULT_SENDER=your-email@gmail.com
     set SECRET_KEY=your-secret-key
     ```
   - macOS/Linux:
     ```
     export MAIL_USERNAME=your-email@gmail.com
     export MAIL_PASSWORD=your-app-password
     export MAIL_DEFAULT_SENDER=your-email@gmail.com
     export SECRET_KEY=your-secret-key
     ```

   Для Gmail вам потребуется:
   - Включить двухфакторную аутентификацию
   - Создать пароль приложения в настройках безопасности Google Account

   Альтернативно, вы можете напрямую отредактировать файл `app.py` с вашими учетными данными (только для разработки, не рекомендуется для продакшена).

6. **Инициализировать базу данных**
   ```
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Запустить приложение**
   ```
   python app.py
   ```

8. **Доступ к приложению**
   
   Откройте браузер и перейдите по адресу `http://127.0.0.1:5000`

### Развертывание в продакшен

1. **Обновить настройки безопасности**
   
   Отредактируйте `app.py`, чтобы включить защищенные куки:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   ```

2. **Установить переменные окружения на вашем сервере**
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   SECRET_KEY=your-secret-key
   ```

3. **Отключить режим отладки**
   
   Установите `debug=False` в вызове `app.run()` или используйте переменную окружения.

4. **Использовать производственный WSGI-сервер**
   
   Для развертывания с Gunicorn (включен в requirements.txt):
   ```
   gunicorn app:app
   ```

5. **Настроить обратный прокси**
   
   Настройте Nginx или Apache для проксирования запросов к вашему Flask-приложению.

6. **Настроить SSL/TLS**
   
   Получите и настройте SSL-сертификат для безопасной связи. 