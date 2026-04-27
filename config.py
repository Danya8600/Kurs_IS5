from pathlib import Path


class Config:
    """
    Класс с основными настройками Flask-приложения.
    Здесь хранятся пути к папкам, допустимые расширения файлов
    и базовые параметры анализа.
    """

    # Корневая папка проекта
    BASE_DIR = Path(__file__).resolve().parent

    # Папки для хранения пользовательских файлов
    STORAGE_DIR = BASE_DIR / "storage"
    UPLOAD_FOLDER = STORAGE_DIR / "uploads"
    REPORT_FOLDER = STORAGE_DIR / "reports"
    TEMPLATE_FOLDER = STORAGE_DIR / "templates"

    # Допустимые расширения загружаемых файлов
    ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}

    # Максимальный размер загружаемого файла: 10 МБ
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # Стандартный уровень значимости для ANOVA
    DEFAULT_ALPHA = 0.05

    # Секретный ключ Flask.
    # Нужен для flash-сообщений, сессий и защиты форм.
    SECRET_KEY = "anova-student-app-secret-key"