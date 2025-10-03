from django.contrib import admin
from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig


class AdminConfig(DjangoAdminConfig):
    """ Определите пользовательское приложение администратора."""
    default_site = 'apps.admin.site.AdminSite'

    def ready(self):
        """ Удалите ненужные панели администратора.
        Также переопределите fcm admin.
        """
        super().ready()
        # Импортируйте здесь, когда приложение администратора будет готово
        from django.contrib.auth.models import Group

        from rest_framework.authtoken.models import Token

        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import (
            SocialAccount,
            SocialApp,
            SocialToken,
        )
        from taggit.models import Tag

        # Импорт для переопределения административных панелей
        from ..utils.celery_beat import admin as celery_beat_admin  # noqa
        from ..utils.fcm import admin as fcm_admin  # noqa

        admin_panes_to_remove = (
            EmailAddress,
            Token,
            Group,
            Tag,
            SocialAccount,
            SocialApp,
            SocialToken
        )
        for model in admin_panes_to_remove:
            try:
                admin.site.unregister(model)
            except admin.sites.NotRegistered:
                pass
