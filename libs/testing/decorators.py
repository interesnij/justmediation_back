from django.conf import settings


def assert_not_testing(func):
    """ Декоратор проверяет, что никакие реальные вызовы API не выполняются
    Должен использоваться в других клиентах API, чтобы вызвать ошибку в случае реального API
    вызовы при тестировании
    """

    def _wrapped(*args, **kwargs):
        if settings.TESTING:
            raise RuntimeError('Real API requests during testing')
        return func(*args, **kwargs)
    return _wrapped
