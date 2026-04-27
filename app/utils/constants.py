STUDENT_COLUMN = "ФИО студента"
GROUP_COLUMN = "Группа"
DISCIPLINE_COLUMN = "Дисциплина"
METHOD_COLUMN = "Метод обучения"
SCORE_COLUMN = "Оценка / балл за тест"

REQUIRED_COLUMNS = [
    STUDENT_COLUMN,
    GROUP_COLUMN,
    DISCIPLINE_COLUMN,
    METHOD_COLUMN,
    SCORE_COLUMN,
]

TEXT_COLUMNS = [
    STUDENT_COLUMN,
    GROUP_COLUMN,
    DISCIPLINE_COLUMN,
    METHOD_COLUMN,
]

COLUMN_DESCRIPTIONS = [
    {
        "name": STUDENT_COLUMN,
        "type": "текст",
        "badge": "gray",
    },
    {
        "name": GROUP_COLUMN,
        "type": "текст",
        "badge": "gray",
    },
    {
        "name": DISCIPLINE_COLUMN,
        "type": "текст",
        "badge": "gray",
    },
    {
        "name": METHOD_COLUMN,
        "type": "фактор",
        "badge": "blue",
    },
    {
        "name": SCORE_COLUMN,
        "type": "число",
        "badge": "green",
    },
]

COLUMN_KEYS = {
    "student": STUDENT_COLUMN,
    "group": GROUP_COLUMN,
    "discipline": DISCIPLINE_COLUMN,
    "method": METHOD_COLUMN,
    "score": SCORE_COLUMN,
}