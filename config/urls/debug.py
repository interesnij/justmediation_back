from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

# Debug urls
urlpatterns = []


# adding urls for demonstration or fake apps
# this code adds urls for fake apps to this endpoints:
#   for web UI:
#      /demo/{application_label}/
#   for API:
#      /api/v1/demo/{application_label}/
# if you want to add your fake application, you should
# inherit your application config from libs.apps.FakeAppConfig and
# define property app_urls and api_urls with paths to your urls modules.
if settings.TESTING or settings.DEBUG:
    from django.apps import apps

    from libs.apps import is_fake_app
    for app_label, app_config in apps.app_configs.items():
        # we works here just with fake applications
        if not is_fake_app(app_config):
            continue

        # adding application urls
        url_path = 'demo/{}/'.format(app_label)
        if app_config.app_urls:
            urlpatterns += [path(url_path, include(app_config.app_urls))]

        # adding API urls
        api_urls_path = 'api/v1/demo/{}/'.format(app_label)
        if app_config.api_urls:
            urlpatterns += [
                path(api_urls_path, include(app_config.api_urls))
            ]
