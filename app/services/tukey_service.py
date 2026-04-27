import itertools
import math

import pandas as pd
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def run_tukey_hsd(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str,
    alpha: float = 0.05
) -> list[dict]:
    """
    Выполняет post-hoc тест Tukey HSD.

    Тест показывает, какие конкретно группы статистически значимо
    отличаются друг от друга.
    """

    analysis_dataframe = _prepare_tukey_dataframe(
        dataframe=dataframe,
        score_column=score_column,
        factor_column=factor_column
    )

    unique_groups = analysis_dataframe[factor_column].nunique()

    if unique_groups < 2:
        raise ValueError(
            "Для Tukey HSD нужно минимум две группы по выбранному фактору."
        )

    tukey_result = pairwise_tukeyhsd(
        endog=analysis_dataframe[score_column],
        groups=analysis_dataframe[factor_column],
        alpha=alpha
    )

    group_pairs = list(itertools.combinations(tukey_result.groupsunique, 2))

    results = []

    for index, pair in enumerate(group_pairs):
        group_1, group_2 = pair
        mean_difference = float(tukey_result.meandiffs[index])
        p_value = float(tukey_result.pvalues[index])
        lower_bound = float(tukey_result.confint[index][0])
        upper_bound = float(tukey_result.confint[index][1])
        significant = bool(tukey_result.reject[index])

        results.append(
            {
                "group_1": str(group_1),
                "group_2": str(group_2),
                "mean_difference": _format_number(mean_difference),
                "p_value": _format_p_value(p_value),
                "lower_bound": _format_number(lower_bound),
                "upper_bound": _format_number(upper_bound),
                "significant": significant,
                "significant_text": "Да" if significant else "Нет",
            }
        )

    return results


def _prepare_tukey_dataframe(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str
) -> pd.DataFrame:
    """
    Подготавливает данные для Tukey HSD.
    """

    required_columns = [factor_column, score_column]

    for column in required_columns:
        if column not in dataframe.columns:
            raise ValueError(f"В данных отсутствует столбец: {column}")

    analysis_dataframe = dataframe[required_columns].copy()

    analysis_dataframe[score_column] = pd.to_numeric(
        analysis_dataframe[score_column],
        errors="coerce"
    )

    analysis_dataframe = analysis_dataframe.dropna(
        subset=[factor_column, score_column]
    )

    analysis_dataframe[factor_column] = (
        analysis_dataframe[factor_column]
        .astype(str)
        .str.strip()
    )

    analysis_dataframe = analysis_dataframe[
        analysis_dataframe[factor_column] != ""
    ]

    if analysis_dataframe.empty:
        raise ValueError(
            "После очистки данных не осталось строк для Tukey HSD."
        )

    return analysis_dataframe


def _format_number(value, digits: int = 4) -> str:
    """
    Форматирует число для вывода в интерфейсе.
    """

    if value is None:
        return "—"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    if math.isnan(number):
        return "—"

    if math.isinf(number):
        return "∞"

    formatted = f"{number:.{digits}f}"
    formatted = formatted.rstrip("0").rstrip(".")

    return formatted if formatted else "0"


def _format_p_value(value) -> str:
    """
    Форматирует p-value.
    """

    if value is None:
        return "—"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    if math.isnan(number):
        return "—"

    if number < 0.0001:
        return "< 0.0001"

    return _format_number(number, digits=4)