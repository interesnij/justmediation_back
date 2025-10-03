from django import forms
from django.core.paginator import Page
from django.utils.encoding import force_str
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import override_method


class ReducedBrowsableAPIRenderer(BrowsableAPIRenderer):
    """ BrowsableAPIRenderer, который скрывает некоторую информацию.
    Этот рендерер работает и выглядит аналогично рендереру DRF API по умолчанию,
    но не показывайте формы для редактирования данных (эти формы содержат все возможные
    значения), фильтры и строки документов.

    Это полезно для отслеживания проблем с производительностью с помощью панели инструментов 
    отладки, поскольку это позволяет избежать неоптимальной загрузки селекторов в формах 
    DRF "фильтр" и "создать/обновить".
    """

    def get_rendered_html_form(self, data, view, method, request):
        """ Никогда не показывайте никаких форм для редактирования.
        У нас есть много пользовательских полей сериализаторов, которые не поддерживают
        хорошо формируем входные данные, поэтому мы не показываем никаких html-форм
        """
        return

    def get_filter_form(self, data, view, request):
        """ Скрыть форму фильтра
        Здесь мы отключаем форму фильтра для всех методов DRF API для повышения 
        производительности отслеживание.
        Добавление фильтров является проблемой, когда есть фильтр по какому-либо экземпляру, и
        DRF выбирает соответствующие варианты с помощью отдельных запросов, что не является
        оптимальный.
        """
        return

    def show_form_for_method(self, view, method, request, obj):
        """ Скрыть/отобразить форму для необработанного ввода.
        Здесь мы отключаем форму необработанного контента для массовых обновлений
        """
        bulk_update_actions = [
            'bulk_update',
            'partial_bulk_update'
        ]
        res = super().show_form_for_method(view, method, request, obj)

        if getattr(view, 'action', None) in bulk_update_actions:
            return False

        return res

    def get_raw_data_form(self, data, view, method, request):
        """ Переопределите метод для удаления полей, доступных только для чтения, 
        из необработанной формы. Код практически скопирован из источников DRF
        """
        # Смотрите выпуск # 2089 для рефакторинга этого.
        serializer = getattr(data, 'serializer', None)
        if serializer and not getattr(serializer, 'many', False):
            instance = getattr(serializer, 'instance', None)
            if isinstance(instance, Page):
                instance = None
        else:
            instance = None

        with override_method(view, request, method) as fake_request:
            # Проверьте разрешения
            if not self.show_form_for_method(
                    view, method, fake_request, instance):
                return

            # Если возможно, сериализуйте исходное содержимое для общей формы
            default_parser = view.parser_classes[0]
            renderer_class = getattr(default_parser, 'renderer_class', None)
            if hasattr(view, 'get_serializer') and renderer_class:
                # View имеет определенный сериализатор, а класс parser имеет соответствующий 
                # средство визуализации, которое можно использовать для визуализации данных.
                # попробуйте отобразить входные данные пользователя
                if request.method in ['POST', 'PUT', 'PATCH']:
                    serializer_data = request.data
                else:
                    # если он получит запрос - покажет пустые данные по умолчанию
                    if method in ('PUT', 'PATCH'):
                        serializer = view.get_serializer(instance=instance)
                    else:
                        serializer = view.get_serializer()

                    # изменения здесь
                    # удалить недоступные для редактирования поля из данных
                    serializer_data = serializer.data
                    for field_name, field in serializer.fields.items():
                        if field.read_only:
                            serializer_data.pop(field_name, None)

                # Визуализация содержимого необработанных данных
                renderer = renderer_class()
                accepted = self.accepted_media_type
                context = self.renderer_context.copy()
                context['indent'] = 4
                content = force_str(
                    renderer.render(serializer_data, accepted, context)
                )

            else:
                content = None

            # Создайте общую форму, которая включает в себя поле типа содержимого,
            # и поле содержимого.
            media_types = [parser.media_type for parser in view.parser_classes]
            choices = [(media_type, media_type) for media_type in media_types]
            initial = media_types[0]

            class GenericContentForm(forms.Form):
                _content_type = forms.ChoiceField(
                    label='Media type',
                    choices=choices,
                    initial=initial,
                    widget=forms.Select(
                        attrs={'data-override': 'content-type'}
                    )
                )
                _content = forms.CharField(
                    label='Content',
                    widget=forms.Textarea(
                        attrs={'data-override': 'content'}
                    ),
                    initial=content
                )

            return GenericContentForm()

    def get_description(self, view, status_code):
        """ Не показывайте никакого описания для просмотра.
        По умолчанию DRF отображает строку документа view, но наши представления содержат
        описания для разработчиков, поэтому мы скрываем это
        """
        return ''
