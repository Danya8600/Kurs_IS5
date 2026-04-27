from pathlib import Path

from flask import Blueprint, render_template, request, session, send_file

from config import Config
from app.services.anova_service import run_one_way_anova
from app.services.chart_service import build_analysis_charts
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
from app.services.report_service import create_excel_report
from app.services.tukey_service import run_tukey_hsd
from app.utils.constants import (
    COLUMN_DESCRIPTIONS,
    COLUMN_KEYS,
    DISCIPLINE_COLUMN,
    METHOD_COLUMN,
    GROUP_COLUMN,
    SCORE_COLUMN,
)
from app.utils.validators import (
    validate_uploaded_filename,
    validate_file_exists,
)


main_bp = Blueprint("main", __name__)


FACTOR_OPTIONS = [
    {
        "value": METHOD_COLUMN,
        "label": METHOD_COLUMN,
    },
    {
        "value": GROUP_COLUMN,
        "label": GROUP_COLUMN,
    },
]


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

        "selected_discipline": "",
        "selected_factor": METHOD_COLUMN,
        "selected_factor_groups_count": 0,
        "alpha_value": Config.DEFAULT_ALPHA,

        "anova_result": None,
        "tukey_results": [],
        "charts": None,

        "factor_options": FACTOR_OPTIONS,
        "column_descriptions": COLUMN_DESCRIPTIONS,
        "columns": COLUMN_KEYS,
    }

    context.update(kwargs)

    return render_template("index.html", **context)


def build_preview_context(
    dataframe,
    filename: str,
    warnings=None,
    selected_factor: str = METHOD_COLUMN
) -> dict:
    """
    Формирует общий набор данных для экрана предпросмотра.
    Используется после загрузки файла и после запуска анализа.
    """

    if warnings is None:
        warnings = []

    return {
        "file_info": build_file_info(
            filename=filename,
            rows_count=len(dataframe)
        ),
        "metrics": build_metrics(dataframe),
        "preview_rows": get_preview_rows(dataframe),
        "disciplines": get_unique_values(dataframe, DISCIPLINE_COLUMN),
        "warnings": warnings,
        "empty_values_count": count_empty_values(dataframe),
        "selected_factor_groups_count": len(
            get_unique_values(dataframe, selected_factor)
        ),
    }


def parse_alpha(alpha_value: str) -> float:
    """
    Проверяет и преобразует уровень значимости.
    Поддерживает ввод через точку и через запятую.
    """

    if alpha_value is None:
        return Config.DEFAULT_ALPHA

    normalized_value = str(alpha_value).strip().replace(",", ".")

    if normalized_value == "":
        return Config.DEFAULT_ALPHA

    try:
        alpha = float(normalized_value)
    except ValueError as error:
        raise ValueError(
            "Уровень значимости должен быть числом, например 0.05."
        ) from error

    if not 0 < alpha < 1:
        raise ValueError(
            "Уровень значимости должен быть больше 0 и меньше 1."
        )

    return alpha


def validate_factor_column(factor_column: str) -> str:
    """
    Проверяет, что выбранный фактор разрешён для анализа.
    Сейчас поддерживаются:
    - Метод обучения;
    - Группа.
    """

    allowed_factors = [factor["value"] for factor in FACTOR_OPTIONS]

    if factor_column not in allowed_factors:
        raise ValueError("Выбран некорректный фактор для анализа.")

    return factor_column


def load_current_dataframe() -> tuple:
    """
    Загружает из session путь к последнему загруженному файлу
    и заново читает DataFrame.
    """

    uploaded_file_path = session.get("uploaded_file_path")
    uploaded_file_name = session.get("uploaded_file_name")

    if not uploaded_file_path:
        raise ValueError(
            "Сначала загрузите файл с данными."
        )

    file_path = Path(uploaded_file_path)

    validate_file_exists(file_path)

    raw_dataframe = read_data_file(file_path)
    dataframe, warnings = prepare_dataframe(raw_dataframe)

    if not uploaded_file_name:
        uploaded_file_name = file_path.name

    return dataframe, warnings, uploaded_file_name


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

        preview_context = build_preview_context(
            dataframe=dataframe,
            filename=uploaded_file.filename,
            warnings=warnings,
            selected_factor=METHOD_COLUMN
        )

        return render_main_page(
            active_screen="preview",
            file_loaded=True,
            analysis_done=False,
            report_ready=False,
            selected_factor=METHOD_COLUMN,
            **preview_context
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


@main_bp.route("/analyze", methods=["POST"])
def analyze_data():
    """
    Проводит ANOVA и Tukey HSD по последнему загруженному файлу.
    """

    selected_discipline = request.form.get("discipline", "").strip()
    selected_factor = request.form.get("factor_column", METHOD_COLUMN)
    alpha_input = request.form.get("alpha", str(Config.DEFAULT_ALPHA))

    preview_context = {}

    try:
        selected_factor = validate_factor_column(selected_factor)

        dataframe, warnings, uploaded_file_name = load_current_dataframe()

        preview_context = build_preview_context(
            dataframe=dataframe,
            filename=uploaded_file_name,
            warnings=warnings,
            selected_factor=selected_factor
        )

        alpha = parse_alpha(alpha_input)

        analysis_dataframe = dataframe.copy()

        if selected_discipline:
            analysis_dataframe = analysis_dataframe[
                analysis_dataframe[DISCIPLINE_COLUMN] == selected_discipline
            ].copy()

            if analysis_dataframe.empty:
                raise ValueError(
                    "После фильтрации по выбранной дисциплине не осталось данных для анализа."
                )

        anova_result = run_one_way_anova(
            dataframe=analysis_dataframe,
            score_column=SCORE_COLUMN,
            factor_column=selected_factor,
            alpha=alpha
        )

        tukey_results = run_tukey_hsd(
            dataframe=analysis_dataframe,
            score_column=SCORE_COLUMN,
            factor_column=selected_factor,
            alpha=alpha
        )

        charts = build_analysis_charts(
            dataframe=analysis_dataframe,
            score_column=SCORE_COLUMN,
            factor_column=selected_factor
        )

        session["selected_discipline"] = selected_discipline
        session["selected_factor"] = selected_factor
        session["alpha"] = alpha

        return render_main_page(
            active_screen="results",
            file_loaded=True,
            analysis_done=True,
            report_ready=True,

            selected_discipline=selected_discipline,
            selected_factor=selected_factor,
            alpha_value=alpha,

            anova_result=anova_result,
            tukey_results=tukey_results,
            charts=charts,

            **preview_context
        )

    except ValueError as error:
        if preview_context:
            return render_main_page(
                active_screen="preview",
                file_loaded=True,
                analysis_done=False,
                report_ready=False,

                error_message=str(error),
                selected_discipline=selected_discipline,
                selected_factor=selected_factor,
                alpha_value=alpha_input,

                **preview_context
            )

        return render_main_page(
            active_screen="upload",
            file_loaded=False,
            analysis_done=False,
            report_ready=False,
            error_message=str(error),
        )

    except Exception as error:
        if preview_context:
            return render_main_page(
                active_screen="preview",
                file_loaded=True,
                analysis_done=False,
                report_ready=False,

                error_message=(
                    "Произошла непредвиденная ошибка при проведении анализа: "
                    f"{error}"
                ),
                selected_discipline=selected_discipline,
                selected_factor=selected_factor,
                alpha_value=alpha_input,

                **preview_context
            )

        return render_main_page(
            active_screen="upload",
            file_loaded=False,
            analysis_done=False,
            report_ready=False,
            error_message=(
                "Произошла непредвиденная ошибка при проведении анализа: "
                f"{error}"
            ),
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


@main_bp.route("/download-report", methods=["GET"])
def download_report():
    """
    Формирует и отправляет пользователю Excel-отчёт
    по последнему выполненному анализу.
    """

    try:
        dataframe, warnings, uploaded_file_name = load_current_dataframe()

        selected_discipline = session.get("selected_discipline", "")
        selected_factor = session.get("selected_factor", METHOD_COLUMN)
        alpha = session.get("alpha", Config.DEFAULT_ALPHA)

        selected_factor = validate_factor_column(selected_factor)
        alpha = parse_alpha(str(alpha))

        analysis_dataframe = dataframe.copy()

        if selected_discipline:
            analysis_dataframe = analysis_dataframe[
                analysis_dataframe[DISCIPLINE_COLUMN] == selected_discipline
            ].copy()

            if analysis_dataframe.empty:
                raise ValueError(
                    "После фильтрации по выбранной дисциплине не осталось данных для отчёта."
                )

        anova_result = run_one_way_anova(
            dataframe=analysis_dataframe,
            score_column=SCORE_COLUMN,
            factor_column=selected_factor,
            alpha=alpha
        )

        tukey_results = run_tukey_hsd(
            dataframe=analysis_dataframe,
            score_column=SCORE_COLUMN,
            factor_column=selected_factor,
            alpha=alpha
        )

        metrics = build_metrics(analysis_dataframe)

        report_path = create_excel_report(
            report_folder=Config.REPORT_FOLDER,
            filename=uploaded_file_name,
            anova_result=anova_result,
            tukey_results=tukey_results,
            selected_discipline=selected_discipline,
            metrics=metrics,
        )

        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_path.name
        )

    except ValueError as error:
        return render_main_page(
            active_screen="results",
            file_loaded=False,
            analysis_done=False,
            report_ready=False,
            error_message=str(error),
        )

    except Exception as error:
        return render_main_page(
            active_screen="results",
            file_loaded=False,
            analysis_done=False,
            report_ready=False,
            error_message=(
                "Произошла ошибка при формировании отчёта: "
                f"{error}"
            ),
        )