from abc import ABC
from django.utils.translation import gettext_lazy as _
from health_check.backends import BaseHealthCheckBackend


class AbstractHealthCheckBackend(BaseHealthCheckBackend, ABC):
    """ Абстрактная проверка работоспособности для добавления пользовательских методов 
    или переопределения методов. """
    working_status = _('OK')
    _identifier = None
    _description = None

    def pretty_status(self):
        """ Сделайте "ОК" настраиваемым, а не просто "работающим". """
        if self.errors:
            return '\n'.join(str(e) for e in self.errors)
        return self.working_status

    def identifier(self):
        """ Получите идентификатор проверки работоспособности. """
        return self._identifier

    @property
    def description(self):
        """ Идентификатор проверки работоспособности, который может быть отображен 
        пользователю. """
        return self._description
