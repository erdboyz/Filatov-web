# Blog Application with Email Verification

A Flask-based blog application with user authentication, email verification, and admin functionality.

## Live Demo

The application is deployed and accessible at: [https://filatov-web.onrender.com](https://filatov-web.onrender.com)

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
     set MAIL_USERNAME=your-email@example.com
     set MAIL_PASSWORD=your-email-password
     set MAIL_DEFAULT_SENDER=your-email@example.com
     set SECRET_KEY=your-secret-key
     ```
   - macOS/Linux:
     ```
     export MAIL_USERNAME=your-email@example.com
     export MAIL_PASSWORD=your-email-password
     export MAIL_DEFAULT_SENDER=your-email@example.com
     export SECRET_KEY=your-secret-key
     ```

   For most email providers, you'll need to:
   - Enable SMTP access in your email account settings
   - Use application-specific passwords if your account has 2FA enabled
   - Check provider-specific security settings if you encounter authentication issues

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
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
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

### Deployment on Render

This application is configured to run on Render. To deploy your own instance:

1. Fork or clone this repository to your GitHub account
2. Create a new Web Service on Render
3. Connect to your GitHub repository
4. Configure the build command: `chmod +x build.sh && ./build.sh`
5. Configure the start command: `gunicorn app:app`
6. Add the required environment variables mentioned above
7. Deploy

**Note about database persistence on Render:**
When using SQLite with Render, be aware that the filesystem is ephemeral. If you need a persistent database:
- Consider using a managed PostgreSQL database
- Or upgrade to a plan with disk persistence and configure your application to use the persistent directory

---

## Инструкции на русском языке

### Демо-версия

Приложение развернуто и доступно по адресу: [https://filatov-web.onrender.com](https://filatov-web.onrender.com)

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
     set MAIL_USERNAME=your-email@example.com
     set MAIL_PASSWORD=your-email-password
     set MAIL_DEFAULT_SENDER=your-email@example.com
     set SECRET_KEY=your-secret-key
     ```
   - macOS/Linux:
     ```
     export MAIL_USERNAME=your-email@example.com
     export MAIL_PASSWORD=your-email-password
     export MAIL_DEFAULT_SENDER=your-email@example.com
     export SECRET_KEY=your-secret-key
     ```

   Для большинства почтовых сервисов вам потребуется:
   - Включить доступ SMTP в настройках вашей учетной записи электронной почты
   - Использовать специальные пароли приложений, если в вашей учетной записи включена двухфакторная аутентификация
   - Проверить настройки безопасности вашего почтового провайдера при возникновении проблем с аутентификацией

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
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
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

### Развертывание на Render

Это приложение настроено для работы на Render. Чтобы развернуть свой экземпляр:

1. Сделайте форк или клонируйте этот репозиторий в свой аккаунт GitHub
2. Создайте новый Web Service на Render
3. Подключитесь к своему репозиторию GitHub
4. Настройте команду сборки: `chmod +x build.sh && ./build.sh`
5. Настройте команду запуска: `gunicorn app:app`
6. Добавьте необходимые переменные окружения, указанные выше
7. Разверните приложение

**Примечание о сохранении базы данных на Render:**
При использовании SQLite с Render имейте в виду, что файловая система эфемерна. Если вам нужна постоянная база данных:
- Рассмотрите возможность использования управляемой базы данных PostgreSQL
- Или перейдите на тарифный план с постоянным хранилищем и настройте приложение для использования постоянного каталога 