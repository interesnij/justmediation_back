from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_activity_year(year: int):
    """ Подтвердите год деятельности человека.
    Например, год окончания учебы или год трудоустройства.
    Правила:
        Твой выпускной год не может быть из будущего. Например
        текущий год - 2019, но ваш выпускной - 2020.
        Ваш год работы не может быть из далекого прошлого
        (более 100 лет назад).
    """
    cur_year = datetime.now().year
    if year > cur_year or year < cur_year - 100:
        raise ValidationError(
            _('Please, enter valid year.')
        )


def validate_experience_years(years: int):
    """ Подтвердите количество лет опыта.
    Правила:
        У человека не может быть более чем 100-летнего опыта.
    """
    if years > 100:
        raise ValidationError(
            _('Please, enter valid amount of experience years.')
        )
