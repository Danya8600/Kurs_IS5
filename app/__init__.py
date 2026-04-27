from flask import Flask

from config import Config


def create_app():
    """
    Создаёт и настраивает Flask-приложение.
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    # Создаём рабочие папки, если их ещё нет
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    Config.REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    Config.TEMPLATE_FOLDER.mkdir(parents=True, exist_ok=True)

    # Регистрируем маршруты приложения
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app