import math

import pandas as pd
from scipy.stats import f as f_distribution


def run_one_way_anova(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str,
    alpha: float = 0.05
) -> dict:
    """
    Выполняет однофакторный дисперсионный анализ ANOVA.

    score_column — числовой показатель, например оценка / балл за тест.
    factor_column — фактор группировки, например метод обучения.
    alpha — уровень значимости.
    """

    analysis_dataframe = _prepare_analysis_dataframe(
        dataframe=dataframe,
        score_column=score_column,
        factor_column=factor_column
    )

    grouped_data = list(analysis_dataframe.groupby(factor_column, sort=True))

    if len(grouped_data) < 2:
        raise ValueError(
            "Для ANOVA нужно минимум две группы по выбранному фактору."
        )

    total_observations = len(analysis_dataframe)
    groups_count = len(grouped_data)

    df_between = groups_count - 1
    df_within = total_observations - groups_count
    df_total = total_observations - 1

    if df_within <= 0:
        raise ValueError(
            "Недостаточно наблюдений для ANOVA. "
            "Внутри групп должно быть достаточно оценок, чтобы оценить разброс данных."
        )

    grand_mean = analysis_dataframe[score_column].mean()

    ss_between = 0.0
    ss_within = 0.0

    groups_summary = []

    for group_name, group_dataframe in grouped_data:
        scores = group_dataframe[score_column]
        group_count = len(scores)
        group_mean = scores.mean()
        group_std = scores.std(ddof=1)

        ss_between += group_count * ((group_mean - grand_mean) ** 2)
        ss_within += ((scores - group_mean) ** 2).sum()

        groups_summary.append(
            {
                "name": str(group_name),
                "count": int(group_count),
                "mean": _format_number(group_mean, digits=2),
                "std": _format_number(group_std, digits=2),
            }
        )

    ss_total = ss_between + ss_within

    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    if ms_within == 0:
        raise ValueError(
            "Невозможно провести ANOVA: внутри групп нет разброса оценок. "
            "Проверьте, что в каждой группе есть разные значения баллов."
        )

    f_statistic = ms_between / ms_within
    p_value = float(f_distribution.sf(f_statistic, df_between, df_within))

    significant = p_value < alpha

    anova_table = [
        {
            "source": "Между группами",
            "ss": _format_number(ss_between),
            "df": df_between,
            "ms": _format_number(ms_between),
            "f": _format_number(f_statistic),
            "p_value": _format_p_value(p_value),
        },
        {
            "source": "Внутри групп",
            "ss": _format_number(ss_within),
            "df": df_within,
            "ms": _format_number(ms_within),
            "f": "—",
            "p_value": "—",
        },
        {
            "source": "Итого",
            "ss": _format_number(ss_total),
            "df": df_total,
            "ms": "—",
            "f": "—",
            "p_value": "—",
        },
    ]

    if significant:
        conclusion = (
            f"p-value = {_format_p_value(p_value)} меньше уровня значимости {alpha}. "
            "Следовательно, различия между средними значениями групп являются статистически значимыми."
        )
    else:
        conclusion = (
            f"p-value = {_format_p_value(p_value)} больше или равно уровню значимости {alpha}. "
            "Следовательно, статистически значимых различий между средними значениями групп не выявлено."
        )

    return {
        "factor_column": factor_column,
        "score_column": score_column,
        "alpha": alpha,
        "f_statistic": _format_number(f_statistic),
        "p_value": _format_p_value(p_value),
        "significant": significant,
        "result_text": "Значимо" if significant else "Не значимо",
        "conclusion": conclusion,
        "anova_table": anova_table,
        "groups_summary": groups_summary,
    }


def _prepare_analysis_dataframe(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str
) -> pd.DataFrame:
    """
    Подготавливает данные для ANOVA:
    - оставляет только фактор и оценку;
    - удаляет пустые значения;
    - приводит фактор к строке;
    - приводит оценки к числам.
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
            "После очистки данных не осталось строк для анализа."
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
    Форматирует p-value отдельно, чтобы маленькие значения выглядели понятно.
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