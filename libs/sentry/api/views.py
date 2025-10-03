from sentry_sdk import Scope, configure_scope


class SentryMixin:
    """ Микс, который добавляет поддержку sentry для просмотра. """

    def handle_exception(self, exc):
        """ Добавьте оболочку к исключению с помощью области sentry. """
        with configure_scope() as scope:
            self.set_up_scope(scope)
            return super().handle_exception(exc)

    def set_up_scope(self, scope: Scope):
        """ Добавьте дополнительные данные в отчет об ошибке sentry. """
        scope.set_tag('type', 'api')
        scope.set_tag('api_name', self.basename)
        scope.set_tag('api_action', self.action)
