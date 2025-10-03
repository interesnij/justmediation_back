from django.core.mail import get_connection
from health_check.exceptions import ServiceUnavailable
from libs.health_checks.backends.base import AbstractHealthCheckBackend


class EmailHealthCheck(AbstractHealthCheckBackend):
    """Check that email backend is working."""
    _identifier = 'email'
    _description = 'Email Backend Health Check'

    def check_status(self):
        """ Откройте и закройте подключение к почтовому серверу. """
        try:
            connection = get_connection(fail_silently=False)
            connection.timeout = 15
            connection.open()
            connection.close()
        except Exception as error:
            self.add_error(
                error=ServiceUnavailable(error), cause=error
            )
