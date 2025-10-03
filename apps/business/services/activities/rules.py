import typing
from collections.abc import Iterable
from typing import Any
from django.db.models.signals import Signal
from libs.utils import get_lookup_value
from apps.users.models import AppUser
from ... import models

__all__ = (
    'ActivityRule',
    'create_activity',
)


class ActivityRule:
    """Класс для запоминания информации о сигнале, связанном с активностью.

    Атрибуты:
        sender (Signal) - сигнал, который инициирует создание действия
        model (Model) - модель, сигнал которой инициирует создание действия
        msg_template (str) - шаблон сообщения `activity`
        get_user_from_signal (bool) - флаг, который определяет, является ли пользователь
            будет взят из сигнала `kwargs`
        related_user_method (Callable) - метод, связанный с активностью пользователя
        related_user_lookup (str) - поиск по экземплярам активности, связанным с пользователем
        checks (Iterable[Callable]) - повторяющееся количество методов с проверками
            которые проверяют, должно ли быть создано действие
        matter_lookup (str) - поиск по экземплярам, связанным с вопросом

    Лучше определить только один из `related_user_method` или
    `related_user_lookup`. В случае, если заданы оба атрибута, по умолчанию будет
    принят `related_user_method`.
    """
    sender = None
    model = None
    msg_template = None
    get_user_from_signal = False
    related_user_method = None
    related_user_lookup = None
    matter_lookup = None
    checks = []
    user = None
    type = None

    def __init__(
        self, sender: Signal, model: Any, msg_template: str = None,
        get_user_from_signal: bool = False,
        related_user_method: typing.Callable = None,
        related_user_lookup: str = None, checks: Iterable = None,
        matter_lookup: str = None, type: str = None
    ) -> None:
        """ Инициализируйте информацию о правиле основного действия. """
        self.sender = sender or self.sender
        self.model = model or self.model
        self.type = type or self.type
        self.msg_template = msg_template or self.msg_template
        self.get_user_from_signal = get_user_from_signal or self.get_user_from_signal  # noqa
        self.related_user_method = related_user_method or self.related_user_method  # noqa
        self.related_user_method = related_user_method or self.related_user_method  # noqa
        self.related_user_lookup = related_user_lookup or self.related_user_lookup  # noqa
        self.checks = checks or self.checks
        self.matter_lookup = matter_lookup or self.matter_lookup

    def get_rule_user(self, instance: Any) -> AppUser:
        """ Ярлык для получения пользователя, связанного с "активностью". """
        # получить пользователя, связанного с правилом, с помощью метода, если он определен
        if self.related_user_method:
            return self.related_user_method(instance)
        # в противном случае получите пользователя с поиском экземпляра
        return get_lookup_value(instance, self.related_user_lookup)

    def get_rule_matter(self, instance: Any, **kwargs) -> models.Matter:
        """ Короткий путь для получения информации, связанной с "активностью". """
        if not self.matter_lookup:
            return instance
        return get_lookup_value(instance, self.matter_lookup)

    def get_activity_msg(self, instance: Any, **kwargs) -> str:
        # Способ получения сообщения "активность" из шаблона и требуемых параметров.

        if self.get_user_from_signal:
            user = kwargs.get('user')
        else:
            user = self.get_rule_user(instance)
        return self.msg_template.format(user=user.display_name if user else '')


def create_activity(instance: Any, rule: ActivityRule, **kwargs):
    """ Ярлык для создания нового `Действия` на основе правила действия. """
    # выполните все проверки перед созданием реальной активности
    for check in rule.checks:
        is_succeed = check(instance, **kwargs)
        if not is_succeed:
            return
    activity = models.Activity.objects.create(
        matter=rule.get_rule_matter(instance, **kwargs),
        title=rule.get_activity_msg(instance, **kwargs),
        user=rule.get_rule_user(instance),
        type=rule.type
    )
    return activity
