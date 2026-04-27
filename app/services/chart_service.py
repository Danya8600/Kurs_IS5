import pandas as pd
import plotly.express as px
import plotly.io as pio


def build_analysis_charts(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str
) -> dict:
    """
    Строит графики для визуализации результатов ANOVA.

    Возвращает HTML-блоки графиков, которые можно вставлять в шаблон через |safe.
    """

    chart_dataframe = _prepare_chart_dataframe(
        dataframe=dataframe,
        score_column=score_column,
        factor_column=factor_column
    )

    return {
        "mean_chart": build_mean_chart(
            chart_dataframe,
            score_column=score_column,
            factor_column=factor_column
        ),
        "boxplot_chart": build_boxplot_chart(
            chart_dataframe,
            score_column=score_column,
            factor_column=factor_column
        ),
        "histogram_chart": build_histogram_chart(
            chart_dataframe,
            score_column=score_column
        ),
        "count_chart": build_count_chart(
            chart_dataframe,
            factor_column=factor_column
        ),
    }


def build_mean_chart(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str
) -> str:
    """
    Строит столбчатую диаграмму средних значений по группам фактора.
    """

    grouped_dataframe = (
        dataframe
        .groupby(factor_column, as_index=False)[score_column]
        .mean()
        .sort_values(score_column, ascending=False)
    )

    figure = px.bar(
        grouped_dataframe,
        x=factor_column,
        y=score_column,
        text=score_column,
        title=f"Средний балл по фактору «{factor_column}»"
    )

    figure.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    figure.update_layout(
        xaxis_title=factor_column,
        yaxis_title="Средний балл",
        margin=dict(l=30, r=30, t=55, b=40),
        height=360
    )

    return _figure_to_html(figure)


def build_boxplot_chart(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str
) -> str:
    """
    Строит boxplot для отображения разброса оценок по группам.
    """

    figure = px.box(
        dataframe,
        x=factor_column,
        y=score_column,
        points="all",
        title=f"Разброс оценок по фактору «{factor_column}»"
    )

    figure.update_layout(
        xaxis_title=factor_column,
        yaxis_title="Балл",
        margin=dict(l=30, r=30, t=55, b=40),
        height=360
    )

    return _figure_to_html(figure)


def build_histogram_chart(
    dataframe: pd.DataFrame,
    score_column: str
) -> str:
    """
    Строит гистограмму распределения баллов студентов.
    """

    figure = px.histogram(
        dataframe,
        x=score_column,
        nbins=10,
        title="Распределение баллов студентов"
    )

    figure.update_layout(
        xaxis_title="Балл",
        yaxis_title="Количество студентов",
        margin=dict(l=30, r=30, t=55, b=40),
        height=360
    )

    return _figure_to_html(figure)


def build_count_chart(
    dataframe: pd.DataFrame,
    factor_column: str
) -> str:
    """
    Строит диаграмму количества записей по группам выбранного фактора.
    """

    count_dataframe = (
        dataframe[factor_column]
        .value_counts()
        .reset_index()
    )

    count_dataframe.columns = [factor_column, "Количество"]

    figure = px.bar(
        count_dataframe,
        x=factor_column,
        y="Количество",
        text="Количество",
        title=f"Количество записей по фактору «{factor_column}»"
    )

    figure.update_traces(
        texttemplate="%{text}",
        textposition="outside"
    )

    figure.update_layout(
        xaxis_title=factor_column,
        yaxis_title="Количество",
        margin=dict(l=30, r=30, t=55, b=40),
        height=360
    )

    return _figure_to_html(figure)


def _prepare_chart_dataframe(
    dataframe: pd.DataFrame,
    score_column: str,
    factor_column: str
) -> pd.DataFrame:
    """
    Подготавливает данные для построения графиков.
    """

    required_columns = [score_column, factor_column]

    for column in required_columns:
        if column not in dataframe.columns:
            raise ValueError(f"В данных отсутствует столбец для построения графика: {column}")

    chart_dataframe = dataframe[required_columns].copy()

    chart_dataframe[score_column] = pd.to_numeric(
        chart_dataframe[score_column],
        errors="coerce"
    )

    chart_dataframe[factor_column] = (
        chart_dataframe[factor_column]
        .astype(str)
        .str.strip()
    )

    chart_dataframe = chart_dataframe.dropna(
        subset=[score_column, factor_column]
    )

    chart_dataframe = chart_dataframe[
        chart_dataframe[factor_column] != ""
    ]

    if chart_dataframe.empty:
        raise ValueError("После очистки данных не осталось значений для построения графиков.")

    return chart_dataframe


def _figure_to_html(figure) -> str:
    """
    Преобразует Plotly-график в HTML-фрагмент для вставки на страницу.
    """

    return pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs="cdn",
        config={
            "displayModeBar": False,
            "responsive": True
        }
    )