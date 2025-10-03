from drf_yasg.utils import no_body

from ...core.api.utils import define_swagger_auto_schema
from . import views

define_swagger_auto_schema(
    api_view=views.NotificationDispatchViewSet,
    operation_id='read_notification',
    method_name='read',
    request_body=no_body,
    responses={
        204: 'Notification is read',
    }
)

define_swagger_auto_schema(
    api_view=views.NotificationDispatchViewSet,
    operation_id='unread_notification',
    method_name='unread',
    request_body=no_body,
    responses={
        204: 'Notification is unread',
    }
)
