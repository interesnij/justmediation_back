import platform
from collections import namedtuple
import django
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from constance import config
from ..docs import get_changelog_preview
from ..utils import get_base_url, get_latest_version


Changelog = namedtuple(
    'Changelog', ['name', 'text', 'version', 'swagger_url', 'docs_url']
)

api_configs = {
    'backend': settings.API_INFO_BACKEND,
}


def load_app_info():
    """ Информация о приложении. """
    return dict(
        env=settings.ENVIRONMENT,
        version=get_latest_version('changelog_backend/changelog.md'),
        python_version=platform.python_version(),
        django_version=django.get_version(),
        app_url=get_base_url(),
        app_label=config.APP_LABEL,
    )


class IndexView(TemplateView):
    """ Представление на основе класса для этого показывает версию файла swagger на главной 
    странице. Отображает текущую версию спецификации swagger и список изменений
    """
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        """ Загрузите 3 последних данных журнала изменений из файлов. """
        context = super().get_context_data(**kwargs)
        changelogs = [
            Changelog(
                name=name.title().replace('_', ' '),
                text=get_changelog_preview(
                    f'docs/changelog_{name}/changelog.md',
                    version_amount=4
                ),
                version=api_config.get('default_version'),
                swagger_url=reverse_lazy('schema-swagger-ui'),
                docs_url=f'/docs/changelog_{name}/changelog.html',
            )
            for name, api_config in api_configs.items()
        ]
        context['changelogs'] = changelogs
        context.update(**load_app_info())
        return context


class HealthCheckView(TemplateView):
    """ Отображает текущее состояние приложения. """
    template_name = 'health_check.html'

    def get_context_data(self, **kwargs):
        """ Загрузите статистические данные приложения. """
        context = super().get_context_data(**kwargs)
        context.update(**load_app_info())
        return context
