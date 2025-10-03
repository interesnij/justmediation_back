import logging
from django.conf import settings
from amqp.exceptions import AccessRefused
from health_check.contrib.rabbitmq.backends import \
    RabbitMQHealthCheck as BaseRabbitMQHealthCheck
from health_check.exceptions import ServiceUnavailable
from kombu import Connection
from .base import AbstractHealthCheckBackend


logger = logging.getLogger(__name__)


class RabbitMQHealthCheck(BaseRabbitMQHealthCheck, AbstractHealthCheckBackend):
    """Checks that rabbitmq is working alright."""
    _identifier = 'rabbitmq'
    _description = 'RabbitMQ Health Check'

    def check_status(self):
        """ Переопределение для использования URL-адреса сельдерея """
        logger.debug('Checking for a broker_url on django settings...')

        broker_url = getattr(
            settings, "BROKER_URL", settings.CELERY_BROKER_URL
        )

        logger.debug(
            f'Got {broker_url} as the broker_url. Connecting to rabbit...'
        )

        logger.debug('Attempting to connect to rabbit...')
        try:
            # conn используется в качестве контекста для последующего освобождения 
            # открытых ресурсов 
            with Connection(broker_url) as conn:
                conn.connect()  # исключения могут возникать при вызове connect
        except ConnectionRefusedError as e:
            self.add_error(ServiceUnavailable(
                'Unable to connect to RabbitMQ: Connection was refused.'), e
            )
        except AccessRefused as e:
            self.add_error(ServiceUnavailable(
                'Unable to connect to RabbitMQ: Authentication error.'), e
            )
        except IOError as e:
            self.add_error(ServiceUnavailable('IOError'), e)
        except BaseException as e:
            self.add_error(ServiceUnavailable('Unknown error'), e)
        else:
            logger.debug('Connection established. RabbitMQ is healthy.')
