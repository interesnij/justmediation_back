from django.conf import settings
from django.contrib import admin


def register_in_debug(*args, **kwargs):
    """ Зарегистрируйте администратора модели для режима отладки.
    Когда режим отладки выключен, он возвращает оболочку nothing-do, которая возвращает
    сам украшенный объект.

    Возвращается:
        объект
    """
    if settings.DEBUG:
        return admin.register(*args, **kwargs)
    else:
        def wrapper(admin_class):
            return admin_class
        return wrapper
