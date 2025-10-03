from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
import pytz


class TimezoneMiddleware(MiddlewareMixin):
    """ Сведение промежуточного программного обеспечения к часовому поясу 
    пользователя из запроса. """

    def process_request(self, request):
        """ Обновите статус часового пояса по запросу. """
        try:
            tzname = request.META.get('HTTP_USER_TIMEZONE', None)
            if tzname:
                timezone.activate(pytz.timezone(tzname))
                request.timezone = pytz.timezone(tzname)
            else:
                timezone.deactivate()
        except pytz.UnknownTimeZoneError:
            timezone.deactivate()
