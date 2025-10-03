from django.utils.html import strip_tags

from libs.notifications.email import DefaultEmailNotification


class EmailNotification(DefaultEmailNotification):
    """Used to send notifications mails to it's recipients.

    Notifications resources will prepare html message, so we overridden
    prepare_mail_text method to just strip tags from html_message and return
    html_message and plain_text_content.

    """

    def __init__(
        self,
        subject: str,
        recipient_list: (list, tuple),
        html_message: str
    ):
        """Init notifications class."""
        super().__init__(subject=subject, recipient_list=recipient_list)
        self.html_message = html_message

    def prepare_mail_text(self):
        """Strip tags from html message return messages of both types."""
        plain_text_content = strip_tags(self.html_message)
        return self.html_message, plain_text_content
