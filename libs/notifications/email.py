import logging
import typing
from collections import namedtuple
from urllib.error import HTTPError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


logger = logging.getLogger('django')
EmailFile = namedtuple('EmailFile', ['filename', 'content', 'mimetype'])


class EmailNotification:
    """ Завершение функции django.core send_mail.
    Он использовался для отправки электронной почты с html- и обычным текстовым содержимым. 
    Также это позволяет для хранения данных, относящихся к электронной почте.
    """
    subject = ''
    from_email = ''
    recipient_list = tuple()
    template = ''
    template_context = {}
    files = tuple()
    email_tmpl_context = {}

    def __init__(
        self,
        subject: str = '',
        from_email: str = '',
        recipient_list: typing.Sequence[str] = tuple(),
        template: str = '',
        files: typing.Sequence[EmailFile] = tuple(),
        **template_context
    ):
        """ Инициализация уведомления по электронной почте.
        Аргументы:
            тема(str): Тема электронного письма
            from_email(str): Отправитель электронной почты
            recipient_list(list, tuple): Список получателей электронной почты
            template(str): Путь к html-шаблону электронной почты
            files: typing.Sequence[Email File]: список вложений файла
            template_context(dict): Контекст html-шаблона электронной почты
        """
        self.subject = subject or self.subject
        self.from_email = from_email or self.from_email
        self.recipient_list = recipient_list or self.recipient_list
        self.template = template or self.template
        self.files = files
        self.template_context = template_context or self.template_context
        self.is_subscribed = True

    def get_subject(self):
        """ Укажите тему электронного письма. """
        return self.subject

    def get_formatted_subject(self):
        """ Получите отформатированную тему электронного письма.
        Может использоваться для добавления обычного текста в темы электронной почты.
        """
        return self.get_subject()

    def get_from_email(self):
        """ Получить электронное письмо `sender`."""
        return self.from_email

    def get_recipient_list(self):
        """ Получите получателей электронной почты. """
        return self.recipient_list

    def get_template(self):
        """ Получите шаблон электронного письма. """
        return self.template

    def get_template_context(self):
        """ Получите контекст шаблона электронного письма. """
        return self.template_context

    def get_files(self):
        """ Получайте вложения к файлам электронной почты. """
        return self.files

    def prepare_mail_text(self):
        """ Подготовьте html-содержимое электронного письма (обычный текст и электронная почта)."""
        html_message = render_to_string(
            self.get_template(),
            self.get_template_context()
        )
        plain_text_content = strip_tags(html_message)
        return html_message, plain_text_content

    def prepare_mail_args(self):
        """ Подготовьте аргументы по электронной почте перед отправкой. """
        subject = self.get_formatted_subject()
        html_content, plain_text_content = self.prepare_mail_text()
        from_email = self.get_from_email()
        recipient_list = self.get_recipient_list()
        files = self.get_files()

        return dict(
            subject=subject,
            body=plain_text_content,
            from_email=from_email,
            to=recipient_list,
            html_message=html_content,
            files=files
        )

    def send(self) -> bool:
        """ Отправьте электронное письмо.
        Возвращается:
            True: если это удалось
            False: если это не удалось
        """

        email_args = self.prepare_mail_args()
        html_message = email_args.pop('html_message')
        files = email_args.pop('files')

        mail = EmailMultiAlternatives(**email_args)
        mail.attach_alternative(html_message, 'text/html')

        # Attach files
        for file in files:
            mail.attach(
                filename=file.filename,
                content=file.content,
                mimetype=file.mimetype,
            )

        # Send email
        try:
            if self.is_subscribed:
                mail.send()
                self.on_email_send_succeed()
                return True
            else:
                return False
        except HTTPError as error:
            logger.error(
                f'Error while sending email to {email_args["to"]}: {error}'
            )
            self.on_email_send_failed(error)
            return False

    def on_email_send_succeed(self):
        """ Подключитесь для выполнения действия, когда отправка электронной почты 
        завершится успешно. """

    def on_email_send_failed(self, error: HTTPError):
        """ Подключитесь для выполнения действия, когда не удалось отправить 
        электронное письмо. """


class DefaultEmailNotification(EmailNotification):
    """ Используется для отправки почты с адреса приложения по умолчанию. """
    from_email = settings.DEFAULT_FROM_EMAIL

    def get_formatted_subject(self):
        """ Добавить ярлык приложения к теме """
        return f'{self.get_subject()}'
