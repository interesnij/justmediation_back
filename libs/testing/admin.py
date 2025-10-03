from django.contrib.admin.sites import AdminSite
from django.core.exceptions import FieldError
from django.test import RequestFactory, tag
from django.urls import reverse
from apps.users.factories import AdminAppUserFactory


__all__ = (
    'TestAdminFieldsMixin',
    'TestRelatedObjectActionsMixin',
    'TestInitialValuesAdminMixin',
    'TestDisabledFieldsMixin',
)


@tag('admin')
class AdminTestShortcuts(object):
    """ Класс с ярлыками для администратора тестируемой модели. """
    factory = None
    model_admin = None
    _factory = RequestFactory()

    def setUp(self):
        super().setUp()
        assert self.factory, '`factory` attribute is not specified.'
        assert self.model_admin, '`model_admin` attribute is not specified.'

    def get_model(self):
        """ Ярлык для получения модели с помощью factory. """
        return self.factory._meta.model

    def get_admin_instance(self):
        """ Возвращает экземпляр класса admin """
        return self.model_admin(self.get_model(), AdminSite())

    def get_add_view_url(self):
        """ Возвращает URL-адрес для добавления объекта в представление. """
        url_name = (
            'admin:{meta.app_label}_{meta.model_name}_add'
            .format(meta=self.get_model()._meta)
        )
        return reverse(url_name)

    def get_change_view_url(self, obj):
        """ Возвращает URL-адрес для изменения представления объекта. """
        url_name = (
            'admin:{meta.app_label}_{meta.model_name}_change'
            .format(meta=self.get_model()._meta)
        )
        return reverse(url_name, args=(obj.pk,))

    def get_changelist_view_url(self):
        """ Возвращает URL-адрес для просмотра списка изменений объекта. """
        url_name = (
            'admin:{meta.app_label}_{meta.model_name}_changelist'
            .format(meta=self.get_model()._meta)
        )
        return reverse(url_name)

    def get_delete_view_url(self, obj):
        """ Возвращает URL-адрес для просмотра удаления объекта. """
        url_name = (
            'admin:{meta.app_label}_{meta.model_name}_delete'
            .format(meta=self.get_model()._meta)
        )
        return reverse(url_name, args=(obj.pk,))


class TestAdminFieldsMixin(AdminTestShortcuts):
    """ Микширование для тестов классов `ModelAdmin`.
    Пример:
        class TestSampleModelAdminFields(TestAdminFieldsMixin, TestCase):
            factory = SampleModelFactory
            model_admin = SampleModelAdmin

    """

    def test_model_admin_fields(self):
        """ Проверьте правильность реализации Model Admin.
        Проверяет, указаны ли поля, указанные в Model Admin, также
        в самом классе модели.
        """
        try:
            self.get_admin_instance().get_form(self._get_request())
        except FieldError as e:
            admin = self.model_admin
            model = self.get_model()
            msg = (
                '\'{0}\' fieldset is not relevant to \'{1}\' model.\n{2}'
                .format(admin.__name__, model.__name__, e)
            )
            raise AssertionError(msg) from None

    def _get_request(self):
        """ Ярлык для насмешливого объекта запроса """
        request = self._factory.get('/')
        setattr(request, 'META', {'QUERY_STRING': ''})
        return request


class TestRelatedObjectActionsMixin(AdminTestShortcuts):
    """ Микширование для тестирования `Связанного объекта ActionsMixin`.
    Пример:
        class EventAdminTest(TestRelatedObjectActionsMixin, TestCase):
            factory = EventFactory
            model_admin = EventAdmin

    Применяется в тестах администратора расписания
    """

    def test_related_admin_links(self):
        """ Проверьте на `Смешивание действий связанных объектов`.
        Убедитесь, что ссылки на связанные действия объекта сохраняются в ответе.
        """
        self.client.force_login(AdminAppUserFactory())
        obj = self.factory()
        url = self.get_change_view_url(obj)
        response_html = self.client.get(url).rendered_content

        for related_model in self.get_admin_instance().related_models:
            expected_html = 'title="{}"'.format(
                related_model._meta.verbose_name_plural
            )
            self.assertIn(expected_html, response_html)


class TestInitialValuesAdminMixin(AdminTestShortcuts):
    """ Микширование для тестирования `Initial Values AdminMixin`.
    Пример:
        class TestDiscussionThreadAdmin(TestInitialValuesAdminMixin, TestCase):
            factory = DiscussionThreadFactory
            model_admin = DiscussionThreadAdmin
            field_with_initial_value = 'module'

    Применяется в тестах администратора расписания

    """
    field_with_initial_value = None

    def setUp(self):
        super().setUp()
        assert self.field_with_initial_value, (
            '`field_with_initial_value` attribute is not specified.'
        )

    def test_initial_values_in_admin(self):
        """ Проверьте `AdminMixin начальных значений`.
        Убедитесь, что страница "Добавить объект" содержит предварительно выбранный атрибут.
        """
        # Создайте новый экземпляр и получите его исследуемый атрибут
        instance = self.factory()
        attribute = self._get_field_attribute(instance)

        # Создайте запрос на страницу `Добавить объект`
        filtered_url = self._get_filtered_url(attribute)
        request = RequestFactory().get(filtered_url)

        # Получите форму администратора, используя созданный запрос, и получите указанное поле
        admin_form = self.get_admin_instance().get_form(request)
        admin_field = admin_form.base_fields[self.field_with_initial_value]

        # Утверждайте, что начальное значение поля равно указанному экземпляру
        self.assertEqual(admin_field.initial, attribute)

    def _get_field_attribute(self, obj):
        """ Ярлык для получения атрибута `field_with_initial_value` для `obj`. """
        return getattr(obj, self.field_with_initial_value)

    def _get_filtered_url(self, attribute):
        """ Способ получения URL-адреса страницы администратора "Добавить объект" с фильтром. """
        # Получить URL-адрес страницы `Добавить объект`
        url = self.get_add_view_url()

        # Вручную добавьте "changelist_filters" в URL-адрес
        field = self._get_field_attribute(self.get_model()).field
        params_dict = field.get_forward_related_filter(attribute)

        # {'module__module_ptr': 123} -> 'module__module_ptr__exact=123'
        params_str = ''.join(
            '{}__exact={}'.format(key, val) for key, val in params_dict.items()
        )

        # Создайте новый URL, используя исходный URL и "changelist_filters`
        changelist_filters = '?_changelist_filters={}'.format(params_str)
        return url + changelist_filters


class TestDisabledFieldsMixin(AdminTestShortcuts):
    """ Смешайте для тестирования `Смешивание отключенных полей`.
    Пример:
        class TestDiscussionThreadAdmin(TestDisabledFieldsMixin, TestCase):
            factory = DiscussionThreadFactory
            model_admin = DiscussionThreadAdmin

    Applied in schedule admin tests
    """

    def test_fields_are_enabled_for_new_obj(self):
        """ Проверьте, что `disabled_fields` включены в режиме добавления. """
        url = self.get_add_view_url()
        request = RequestFactory().get(url)
        admin_form = self.get_admin_instance().get_form(request, None)
        self.assertFieldsAreDisabled(admin_form, False)

    def test_fields_are_disabled_for_existing_obj(self):
        """ Проверьте, что `disabled_fields` отключены в режиме изменения. """
        obj = self.factory()
        url = self.get_change_view_url(obj)
        request = RequestFactory().get(url)
        admin_form = self.get_admin_instance().get_form(request, obj)
        self.assertFieldsAreDisabled(admin_form, True)

    def assertFieldsAreDisabled(self, form, are_disabled):
        """ Проверьте, отключен ли /включен ли виджет для `disabled_fields`. """
        for field in self.model_admin.disabled_fields:
            field = form.base_fields[field]
            self.assertEqual(field.disabled, are_disabled)
