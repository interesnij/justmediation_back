from itertools import chain
from django.conf.urls import url
from django_object_actions import DjangoObjectActions
from django_object_actions.utils import ChangeActionView, ChangeListActionView


class BaseObjectActionsMixin(DjangoObjectActions):
    """ Mixin, который предоставляет функциональность добавления `base_change_actions`.
    """
    base_change_actions = []

    def _get_action_urls(self):
        """ Зарегистрируйте URL-адреса `base_change_actions`.
        Почти оригинальный метод с изменением в добавлении `base_change_actions`
        в 84 строке.
        """
        actions = {}

        model_name = self.model._meta.model_name
        # e.g.: polls_poll
        base_url_name = "%s_%s" % (self.model._meta.app_label, model_name)
        # e.g.: polls_poll_actions
        model_actions_url_name = "%s_actions" % base_url_name

        self.tools_view_name = "admin:" + model_actions_url_name

        # основное изменение здесь - добавлены URL-адреса `base_change_actions` и
        # `related_models_change_actions`
        all_actions = chain(
            self.change_actions,
            getattr(self, 'related_models_change_actions', []),
            self.changelist_actions,
            self.base_change_actions
        )
        for action in all_actions:
            actions[action] = getattr(self, action)
        return [
            # изменение, поддерживает те же pks, что и администратор
            # https://github.com/django/django/blob/stable/1.10.x/django/
            # contrib/admin/options.py#L555
            url(
                r"^(?P<pk>.+)/actions/(?P<tool>\w+)/$",
                self.admin_site.admin_view(  # checks permissions
                    ChangeActionView.as_view(
                        model=self.model,
                        actions=actions,
                        back="admin:%s_change" % base_url_name,
                        current_app=self.admin_site.name,
                    )
                ),
                name=model_actions_url_name,
            ),
            # список изменений
            url(
                r"^actions/(?P<tool>\w+)/$",
                self.admin_site.admin_view(  # checks permissions
                    ChangeListActionView.as_view(
                        model=self.model,
                        actions=actions,
                        back="admin:%s_changelist" % base_url_name,
                        current_app=self.admin_site.name,
                    )
                ),
                # Дурацкое имя - это прекрасно. https://code.djangoproject.com/ticket/
                # 14259
                name=model_actions_url_name,
            ),
        ]
