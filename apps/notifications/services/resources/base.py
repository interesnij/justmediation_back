import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.forms import model_to_dict
from django.template import Context, Template
from django.template.loader import render_to_string

from rest_framework.exceptions import APIException

from libs.utils import get_base_url

from ....core.models import BaseModel
from ... import models

logger = logging.getLogger('django')


class BaseNotificationResource:
    """ Базовый класс уведомлений.
    Этот класс используется для создания представления данных для уведомлений.

    Атрибуты:
        signal (class): сигнал, на который реагирует уведомление
        instance_type (class): Класс модели, с которым ресурс может работать
        notification_type (NotificationType): Тип уведомления
        runtime_tag (str): runtime_tag типа уведомления
        instance (BaseModel): Тот, который вызвал уведомление.(Обычно это экземпляр
            таких моделей, как Event, Matter, MatterPost)
        recipients (QuerySet):
            Набор запросов пользователей приложений (извлеченных, например), которые получат
            уведомления (в зависимости от настроек)
        title (str): Заголовок уведомления
        web_content_template (str): Путь к шаблону содержимого уведомления, 
            который будет использоваться командой интерфейса
        push_content_template(str):
            Путь к шаблону push-уведомления. Используется в push
            уведомления, отправляемые firebase
        email_subject_template(str): шаблон для создания текста темы электронного письма
        email_content_template(str): Путь к html-шаблону для содержимого уведомления 
            по электронной почте. Используется для создание html-контента для уведомлений 
            по электронной почте
    """
    signal = None
    instance_type = None
    runtime_tag: str = None
    title: str = None
    web_content_template: str = None
    push_content_template: str = None
    email_subject_template: str = None
    email_content_template: str = None
    deep_link_template: str = None
    id_attr_path: str = None

    def __init__(self, instance: BaseModel, **kwargs):
        """ Инициализируйте ресурс уведомления. """
        self.notification_type = models.NotificationType.objects.get(
            runtime_tag=self.runtime_tag
        )
        if not isinstance(instance, self.instance_type):
            raise TypeError(
                f'Resource `{self.__class__.__name__}` can only work with '
                f'`{self.instance_type.__name__}` model'
            )
        self.instance: BaseModel = instance
        self.recipients = self.get_recipients()

    def get_recipients(self) -> QuerySet:
        """ Получайте получателей уведомлений из экземпляра. """
        raise NotImplementedError

    def get_notification_extra_payload(self) -> dict:
        """ Получайте уведомления с дополнительной полезной нагрузкой. """
        return {}

    @classmethod
    def get_deep_link(cls, payload: dict) -> str:
        """ Создайте глубокую ссылку. """
        return cls.deep_link_template.format(
            base_url=get_base_url(),
            id=getattr(payload['instance'], cls.id_attr_path)
        )

    @classmethod
    def prepare_payload(
        cls,
        notification: models.Notification,
        **kwargs
    ) -> dict:
        """ Подготовьте полезную нагрузку уведомления для шаблонов. """
        payload = dict(
            notification_type=notification.type,
        )
        if notification.extra_payload:
            payload.update(**notification.extra_payload)
        try:
            instance = notification.content_object
            # если экземпляра нет, попробуйте получить его вручную из базы данных
            if not instance:
                instance = notification.content_type.get_object_for_this_type(
                    pk=notification.object_id
                )
            payload['instance'] = instance
        except ObjectDoesNotExist:
            logger.warning(
                "Notification trigger object doesn't exist"
            )
            payload['instance'] = None
        payload.update(**kwargs)
        try:
            payload['deep_link'] = cls.get_deep_link(payload)
        except Exception as e:
            raise APIException('{0}: notification={1}'.format(
                str(e),
                json.dumps(model_to_dict(notification)))
            )
        return payload

    @classmethod
    def render_template(
        cls,
        notification: models.Notification,
        template: str,
        is_file=True,
        **kwargs
    ) -> str:
        """ Отрисовка шаблона на основе полезной нагрузки уведомления.
        Установите is_file = False, если передается шаблон str(не путь к шаблону)
        """
        payload = cls.prepare_payload(notification, **kwargs)
        if is_file:
            return render_to_string(
                template_name=template,
                context=payload
            ).strip()
        context = Context(payload)
        return Template(template).render(context=context).strip()

    @classmethod
    def get_web_notification_content(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """ Получите содержимое уведомления (сообщение) для веб-уведомления. """
        return cls.render_template(
            notification=notification,
            template=cls.web_content_template,
            **kwargs,
        )

    @classmethod
    def get_push_notification_content(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """ Получите содержимое уведомления (сообщение) для push-уведомления. """
        return cls.render_template(
            notification=notification,
            template=cls.push_content_template,
            **kwargs,
        )

    @classmethod
    def get_email_subject(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """ Получите текст темы электронного письма. """
        return cls.render_template(
            notification=notification,
            template=cls.email_subject_template,
            is_file=False,
            **kwargs,
        )

    @classmethod
    def get_email_notification_content(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """ Получите содержимое уведомления (сообщение) для уведомления 
        по электронной почте. """
        return cls.render_template(
            notification=notification,
            template=cls.email_content_template,
            **kwargs,
        )
