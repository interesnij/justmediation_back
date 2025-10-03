from urllib.parse import urlencode
from django.forms.models import _get_foreign_key as get_foreign_key
from django.http import HttpResponseRedirect
from django.urls import reverse
from django_object_actions import DjangoObjectActions


class RelatedObjectActionsMixin(DjangoObjectActions):
    """ Смешивание действий связанных объектов.

    Этот микс используется для добавления кнопок ссылок в список изменений для связанных моделей
    к родительскому классу администратора.

    Для использования mixing необходимо добавить в класс Admin атрибут mixing и
    `related_models`:
        class Conference Admin(Related Object ActionsMixin, admin.ModelAdmin):
            # ...
            related_models = (баннер,)

    Также объекты `related_models` могут быть кортежем, а не просто моделью. В этом
    случае смешивание будет искать конкретное поле в модели (вместо того, чтобы находить его
    автоматически). Например, у "Баннера" есть поле внешнего ключа "конференция":

        related_models = (Banner,)

    Кнопки добавлены с помощью действий с объектами Django. Смотрите метод `change_actions`.

    Примечание: `related_models` является обязательным атрибутом, но если вы хотите пропустить 
    его, то установите `related_models = False`.

    Атрибуты:
        related_models (tuple): кортеж связанных определений моделей.

    """
    related_models = []

    def get_change_actions(self, request, object_id, form_url):
        """ Объедините определенные действия по изменению и действия связанных моделей. """
        return super().get_change_actions(
            request, object_id, form_url
        ) + self.related_models_change_actions

    @property
    def related_models_change_actions(self):
        return self.get_related_models_change_actions()

    def get_related_models_change_actions(self):
        """ Немного волшебства для добавления ссылок на связанных администраторов.
        Это должно быть свойство, содержащее список всех доступных действий по изменению
        для модели. Но здесь мы создаем его динамически.

        Логика:
            * возьмите все связанные модели
            * создайте ** новый ** метод `self`, который перенаправляет на соответствующего 
                администратора
            * возвращаемый список строк

        Этот метод вызывается несколько раз, поэтому необходимо проверить, что
        tools не регистрируется дважды.
        """
        related_models_change_actions = []

        for related_model_definition in self.related_models:
            # Если определение модели представляет собой кортеж/список, то существует fk_name
            if type(related_model_definition) in (tuple, list):
                related_model, fk_name = related_model_definition
            # В противном случае fk_field будет получено автоматически
            else:
                related_model, fk_name = related_model_definition, None

            related_model_name = related_model._meta.verbose_name_plural

            method_name = 'tool_redirect_to_{}'.format(
                related_model._meta.model_name
            )
            if method_name in related_models_change_actions:
                continue

            # Получить URL-адрес "списка изменений` для модели
            changelist_url = 'admin:{0}_{1}_changelist'.format(
                related_model._meta.app_label,
                related_model._meta.model_name,
            )

            # Преобразуем поле внешнего ключа `related_model` в `self.model`
            fk_field = get_foreign_key(
                parent_model=self.model,
                model=related_model,
                fk_name=fk_name
            )

            def view_template(
                self, request, obj, fk_field=fk_field,
                changelist_url=changelist_url
            ):
                """ Шаблон действия объекта, который будет добавлен к этому администратору.
                Просто перенаправляет пользователя на `filtered_url`.
                """
                filter_arg = urlencode(
                    fk_field.get_forward_related_filter(obj)
                )
                filtered_url = (
                    '{changelist_url}?{filter_arg}'
                    .format(
                        changelist_url=reverse(changelist_url),
                        filter_arg=filter_arg.replace('=', '__exact=')
                    )
                )
                return HttpResponseRedirect(filtered_url)

            view_template.label = related_model_name
            view_template.short_description = related_model_name

            method_name = 'tool_redirect_to_{}'.format(
                related_model._meta.model_name
            )
            setattr(self.__class__, method_name, view_template)
            related_models_change_actions.append(method_name)

        return list(related_models_change_actions)
