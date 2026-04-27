from flask import Blueprint, render_template, request, session, send_file

from config import Config
from app.services.data_service import (
    prepare_dataframe,
    build_metrics,
    get_preview_rows,
    get_unique_values,
    build_file_info,
    count_empty_values,
)
from app.services.file_service import (
    save_uploaded_file,
    read_data_file,
    create_template_file,
)
from app.utils.constants import (
    COLUMN_DESCRIPTIONS,
    COLUMN_KEYS,
    DISCIPLINE_COLUMN,
)
from app.utils.validators import validate_uploaded_filename


main_bp = Blueprint("main", __name__)


def render_main_page(**kwargs):
    """
    Рендерит единую главную страницу приложения.
    Здесь задаются значения по умолчанию, чтобы шаблон не ломался,
    если какие-то данные ещё не сформированы.
    """

    context = {
        "active_screen": "upload",

        "file_loaded": False,
        "analysis_done": False,
        "report_ready": False,

        "file_info": None,
        "metrics": None,
        "preview_rows": [],
        "disciplines": [],

        "warnings": [],
        "error_message": None,
        "empty_values_count": 0,

        "column_descriptions": COLUMN_DESCRIPTIONS,
        "columns": COLUMN_KEYS,
    }

    context.update(kwargs)

    return render_template("index.html", **context)


@main_bp.route("/", methods=["GET"])
def index():
    """
    Главная страница приложения.
    """

    return render_main_page()


@main_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Загружает файл, читает данные и показывает предпросмотр.
    """

    uploaded_file = request.files.get("data_file")

    try:
        if uploaded_file is None:
            raise ValueError("Файл не был передан на сервер.")

        validate_uploaded_filename(uploaded_file.filename)

        saved_path = save_uploaded_file(
            uploaded_file=uploaded_file,
            upload_folder=Config.UPLOAD_FOLDER
        )

        raw_dataframe = read_data_file(saved_path)
        dataframe, warnings = prepare_dataframe(raw_dataframe)

        session["uploaded_file_path"] = str(saved_path)
        session["uploaded_file_name"] = uploaded_file.filename

        metrics = build_metrics(dataframe)
        preview_rows = get_preview_rows(dataframe)
        disciplines = get_unique_values(dataframe, DISCIPLINE_COLUMN)
        file_info = build_file_info(
            filename=uploaded_file.filename,
            rows_count=len(dataframe)
        )

        return render_main_page(
            active_screen="preview",
            file_loaded=True,
            analysis_done=False,
            report_ready=False,

            file_info=file_info,
            metrics=metrics,
            preview_rows=preview_rows,
            disciplines=disciplines,
            warnings=warnings,
            empty_values_count=count_empty_values(dataframe),
        )

    except ValueError as error:
        return render_main_page(
            active_screen="upload",
            error_message=str(error),
            file_loaded=False,
            analysis_done=False,
            report_ready=False,
        )

    except Exception as error:
        return render_main_page(
            active_screen="upload",
            error_message=(
                "Произошла непредвиденная ошибка при обработке файла: "
                f"{error}"
            ),
            file_loaded=False,
            analysis_done=False,
            report_ready=False,
        )


@main_bp.route("/download-template", methods=["GET"])
def download_template():
    """
    Создаёт и отправляет пользователю Excel-шаблон для заполнения данных.
    """

    template_path = Config.TEMPLATE_FOLDER / "student_results_template.xlsx"

    create_template_file(template_path)

    return send_file(
        template_path,
        as_attachment=True,
        download_name="student_results_template.xlsx"
    )