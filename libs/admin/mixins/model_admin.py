import json
from functools import partial
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

__all__ = (
    'ForbidDeleteAdd',
    'PrettyPrintMixin',
    'FkAdminLink',
    'AllFieldsReadOnly',
    'ForbidChangeMixin',
)


class ForbidChangeMixin(object):
    """ Mixin запрещает изменять разрешение для администратора django. """

    def has_change_permission(self, request, obj=None):
        return False


class ForbidDeleteAdd(object):
    """ Добавлено разрешение запрещать доступ к объектам.
    Сочетание в переопределении двух методов `ModelAdmin` и обоих этих методов
    вернет значение false, не разрешает добавлять и удалять объекты.
    """

    def delete_model(self, request, obj):
        """ Ничего не делайте при удалении. """
        return

    def get_actions(self, request):
        """ Отключите действие "delete_selected". """
        actions = super().get_actions(request)

        if 'delete_selected' in actions:
            del actions['delete_selected']

        return actions

    def has_add_permission(self, request, obj=None):
        """ Убедитесь, что у пользователя есть разрешение на добавление. """
        return False

    def has_delete_permission(self, request, obj=None):
        """ Убедитесь, что у пользователя есть разрешение на удаление. """
        return False


class FkAdminLink(object):
    """ Смешайте, чтобы добавить ссылку на администратора объекта.
    Этот класс может быть унаследован любым другим классом.
    Пример:
        class Book(models.Model):
            author = models.ForeignKey('user')
            content = models.TextField()


        class BookAdmin(models.ModelAdmin, FkAdminLink):
            readonly_fields = ('_author',)

            def _author(self, obj):
                return self._admin_url(obj.author)

            # or with title

            def _author(self, obj):
                return self._admin_url(
                    obj.author,
                    obj.author.last_name + obj.author.first_name[0]
                )

    """

    def _get_admin_url(self, obj):
        content_type = ContentType.objects.get_for_model(
            obj, for_concrete_model=False,
        )
        admin_url_str = (
            f'admin:{content_type.app_label}_{content_type.model}_change'
        )
        return reverse(admin_url_str, args=[obj.pk])

    def _admin_url(self, obj, title=None):
        admin_url = self._get_admin_url(obj)
        return format_html(
            "<a href='{0}' target='_blank'>{1}</a>",
            admin_url, title or str(obj))


class AllFieldsReadOnly(object):
    """Сделайте все поля доступными только для чтения.
    Простое смешивание, если вы хотите сделать все поля доступными только для 
    чтения без указания атрибут полей.
    """

    def get_readonly_fields(self, request, obj=None):
        """ Возвращайте поля с доступом только для чтения. """
        if self.fields:
            return self.fields

        # взял эти исходники django
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)

        if (self.exclude is None and hasattr(self.form, '_meta') and
                self.form._meta.exclude):
            # Учитывайте Meta.exclude пользовательской формы ModelForm только в том случае, 
            # если ModelAdmin не определяет свой собственный.
            exclude.extend(self.form._meta.exclude)

        # если exclude - пустой список, мы передаем None, чтобы он соответствовал
        # default в modelform_factory
        exclude = exclude or None

        defaults = {
            'form': self.form,
            'fields': forms.ALL_FIELDS,
            'exclude': exclude,
            'formfield_callback': partial(
                self.formfield_for_dbfield,
                request=request
            )
        }
        form = modelform_factory(self.model, **defaults)

        return list(form.base_fields)


class PrettyPrintMixin(object):
    """ Микширование для красивого отображения объектов python, доступных только для чтения, 
    в admin. Может использоваться для красивого отображения сложных объектов, таких как 
    dicts, списки. Предоставьте один метод - `pretty_print`
    """

    def pretty_print(self, obj):
        """ Возвращает красивое json-представление ``obj``."""
        return mark_safe(json.dumps(obj, indent=4)
                         .replace(' ', '&nbsp').replace('\n', '<br>'))
