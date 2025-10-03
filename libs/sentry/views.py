from django.shortcuts import render
from sentry_sdk import last_event_id


def handler500(request, *args, **argv):
    """ Показать пользовательскую страницу с ошибкой 500 с формой отчета sentry.
    Использование:
        Просто добавьте это в настройки вашего URL-адреса:
        handler500 = 'libs.sentry.views.handler500'
    """
    return render(
        request,
        '500.html',
        {'sentry_event_id': last_event_id()},
        status=500
    )
