from functools import update_wrapper
from django.contrib.admin import AdminSite as DjangoAdminSite
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from constance import config
from .export.statistics import AppStatisticsResource
from .services import get_apps_stats


class AdminSite(DjangoAdminSite):
    """ Наш пользовательский сайт администратора.
    Расширен для настройки индексного представления. В режиме просмотра индекса мы добавили статистику
    панель мониторинга с кнопкой экспорта статистики.
    """

    # Текст для размещения в конце <заголовка> каждой страницы.
    site_title = _(f'JustMediation Administration')

    # Текст для размещения в <h1> каждой страницы.
    site_header = _(f'JustMediation Administration')

    @never_cache
    def index(self, request, extra_context: dict = None):
        """ Отобразить главную страницу индекса администратора,
        В индексе перечислены все установленные приложения, которые были зарегистрированы на
        этом сайте. Также показывает незначительную статистику.
        """
        if not extra_context:
            extra_context = {}
        extra_context.update(**get_apps_stats())
        extra_context['app_label'] = config.APP_LABEL

        return super().index(request, extra_context)

    @never_cache
    def export_dashboard_statistics(self, request):
        """ Загрузите файл со статистикой панели мониторинга. """
        resource = AppStatisticsResource()
        data = resource.export()
        response = resource.get_export_file_response(data=data)
        return response

    def get_urls(self):
        """ Расширьте, чтобы добавить дополнительные URL-адреса для приложения администратора. """

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        urlpatterns = super().get_urls()
        urlpatterns.append(
            path(
                'export_dashboard_statistics',
                wrap(self.export_dashboard_statistics),
                name='export_dashboard_statistics'
            ),
        )
        return urlpatterns
