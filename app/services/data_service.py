import pandas as pd

from app.utils.constants import (
    REQUIRED_COLUMNS,
    TEXT_COLUMNS,
    STUDENT_COLUMN,
    GROUP_COLUMN,
    DISCIPLINE_COLUMN,
    METHOD_COLUMN,
    SCORE_COLUMN,
)
from app.utils.validators import validate_required_columns


def prepare_dataframe(raw_dataframe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Подготавливает DataFrame для дальнейшей работы:
    - очищает названия столбцов;
    - проверяет обязательные столбцы;
    - очищает текстовые значения;
    - преобразует баллы в числа;
    - формирует предупреждения по данным.
    """

    if raw_dataframe.empty:
        raise ValueError("Загруженный файл пустой.")

    dataframe = raw_dataframe.copy()

    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    dataframe = dataframe.dropna(how="all")

    if dataframe.empty:
        raise ValueError("После удаления пустых строк в файле не осталось данных.")

    validate_required_columns(dataframe.columns)

    warnings = []

    for column in TEXT_COLUMNS:
        dataframe[column] = dataframe[column].apply(_normalize_text_value)

    original_score_values = dataframe[SCORE_COLUMN].copy()
    dataframe[SCORE_COLUMN] = pd.to_numeric(
        dataframe[SCORE_COLUMN],
        errors="coerce"
    )

    invalid_score_count = _count_invalid_scores(
        original_score_values,
        dataframe[SCORE_COLUMN]
    )

    if invalid_score_count > 0:
        warnings.append(
            f"Найдено некорректных значений в столбце с баллами: {invalid_score_count}. "
            "Они не будут учитываться при расчётах."
        )

    empty_values_count = count_empty_values(dataframe)

    if empty_values_count > 0:
        warnings.append(
            f"Найдено пустых значений в обязательных столбцах: {empty_values_count}."
        )

    return dataframe, warnings


def build_metrics(dataframe: pd.DataFrame) -> dict:
    """
    Считает краткие показатели для блока предпросмотра.
    """

    valid_scores = dataframe[SCORE_COLUMN].dropna()

    average_score = "—"

    if not valid_scores.empty:
        average_score = round(float(valid_scores.mean()), 2)

    return {
        "records_count": int(len(dataframe)),
        "groups_count": int(_count_unique_not_empty(dataframe[GROUP_COLUMN])),
        "methods_count": int(_count_unique_not_empty(dataframe[METHOD_COLUMN])),
        "average_score": average_score,
    }


def get_preview_rows(dataframe: pd.DataFrame, limit: int = 10) -> list[dict]:
    """
    Возвращает первые строки файла для отображения на странице.
    """

    preview_dataframe = dataframe[REQUIRED_COLUMNS].head(limit).copy()

    preview_dataframe[SCORE_COLUMN] = preview_dataframe[SCORE_COLUMN].apply(
        _format_score
    )

    return preview_dataframe.to_dict(orient="records")


def get_unique_values(dataframe: pd.DataFrame, column: str) -> list[str]:
    """
    Возвращает уникальные непустые значения из указанного столбца.
    """

    if column not in dataframe.columns:
        return []

    values = []

    for value in dataframe[column].dropna().unique():
        normalized_value = str(value).strip()

        if normalized_value:
            values.append(normalized_value)

    return sorted(values)


def count_empty_values(dataframe: pd.DataFrame) -> int:
    """
    Считает количество пустых значений в обязательных столбцах.
    """

    empty_count = 0

    for column in TEXT_COLUMNS:
        empty_count += int((dataframe[column] == "").sum())

    empty_count += int(dataframe[SCORE_COLUMN].isna().sum())

    return empty_count


def build_file_info(filename: str, rows_count: int) -> dict:
    """
    Формирует информацию о загруженном файле для интерфейса.
    """

    return {
        "filename": filename,
        "rows": rows_count,
        "status": "Готов",
    }


def _normalize_text_value(value) -> str:
    """
    Нормализует текстовые ячейки.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def _format_score(value) -> str:
    """
    Красиво форматирует оценку для вывода в таблице.
    """

    if pd.isna(value):
        return ""

    float_value = float(value)

    if float_value.is_integer():
        return str(int(float_value))

    return str(round(float_value, 2))


def _count_unique_not_empty(series: pd.Series) -> int:
    """
    Считает количество уникальных непустых значений.
    """

    cleaned_values = series.dropna().astype(str).str.strip()
    cleaned_values = cleaned_values[cleaned_values != ""]

    return cleaned_values.nunique()


def _count_invalid_scores(original_scores: pd.Series, converted_scores: pd.Series) -> int:
    """
    Считает значения, которые были заполнены, но не смогли преобразоваться в число.
    """

    invalid_count = 0

    for original_value, converted_value in zip(original_scores, converted_scores):
        if pd.isna(original_value):
            continue

        if str(original_value).strip() == "":
            continue

        if pd.isna(converted_value):
            invalid_count += 1

    return invalid_count