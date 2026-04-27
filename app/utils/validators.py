from pathlib import Path

from config import Config
from app.utils.constants import REQUIRED_COLUMNS


def allowed_file(filename: str) -> bool:
    """
    Проверяет, что файл имеет допустимое расширение.
    """

    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in Config.ALLOWED_EXTENSIONS


def validate_uploaded_filename(filename: str) -> None:
    """
    Проверяет имя загружаемого файла.
    Если файл некорректный, выбрасывает ValueError.
    """

    if not filename:
        raise ValueError("Файл не выбран.")

    if not allowed_file(filename):
        allowed = ", ".join(sorted(Config.ALLOWED_EXTENSIONS))
        raise ValueError(f"Недопустимый формат файла. Разрешены только: {allowed}.")


def validate_required_columns(columns) -> None:
    """
    Проверяет наличие обязательных столбцов в загруженном файле.
    """

    normalized_columns = [str(column).strip() for column in columns]

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in normalized_columns
    ]

    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            "В файле отсутствуют обязательные столбцы: "
            f"{missing}. Проверьте структуру файла или скачайте шаблон."
        )


def validate_file_exists(path: Path) -> None:
    """
    Проверяет, существует ли файл на диске.
    """

    if not path.exists() or not path.is_file():
        raise ValueError("Файл не найден. Попробуйте загрузить его повторно.")