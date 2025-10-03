from urllib.parse import parse_qsl
from django.contrib import admin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from ..core.admin import BaseAdmin
from ..documents import models


class ResourceAdminMixin:
    """ Общая логика для панелей администрирования моделей ресурсов """

    def get_readonly_fields(self, request, obj=None):
        """ Установите поля owner и matter для чтения только в том случае, 
        если obj является шаблоном. """
        readonly_fields = super().get_readonly_fields(
            request,
            obj
        )
        if not obj or not obj.is_template:
            return readonly_fields
        return readonly_fields + ('matter', 'owner')

    def get_changeform_initial_data(self, request) -> dict:
        """ Установите инициалы из _changelist_filters.
        Это использовалось для установки исходных данных в форме администратора, 
        когда мы пытались создать документ из отфильтрованного набора запросов. 
        Например, когда мы получим все документы из одной папки и пытаюсь 
        добавить другую.
        """
        data = super().get_changeform_initial_data(request)
        data['created_by'] = request.user.pk
        if '_changelist_filters' in request.GET:
            query = request.GET['_changelist_filters']
            query = query.replace('__id__exact', '').replace('__exact', '')
            query_params = dict(parse_qsl(query))
            data.update(**query_params)
        return data


@admin.register(models.Document)
class DocumentAdmin(ResourceAdminMixin, BaseAdmin):
    """Admin panel for `Document` model."""
    autocomplete_fields = (
        'parent',
    )
    list_display = (
        'title',
        'parent',
        'owner',
        'matter',
        'created_by',
        'is_template',
        'created',
        'modified',
    )
    search_fields = ('title',)
    list_filter = (
        'is_template',
        'mime_type',
    )
    autocomplete_list_filter = (
        'owner',
        'matter',
        'parent',
        'created_by',
    )
    ordering = (
        'created_by',
        'created',
        'modified'
    )
    fieldsets = (
        (_('Folder'), {
            'fields': (
                'parent',
            )
        }),
        (_('Main info'), {
            'fields': (
                'title',
                'is_template',
                'mime_type',
                'file',
                'uuid',
                'transaction_id',
                'md5',
            )
        }),
    )
    readonly_fields = (
        'mime_type',
        'is_template',
        'created_by',
        'uuid',
        'file',
        'transaction_id',
        'md5',
    )
    list_select_related = (
        'matter',
        'owner',
        'parent',
        'created_by',
    )

    def save_model(self, request, obj, form, change):
        """ `created_by` для только что созданных документов. """
        if not change:
            obj.created_by = request.user
        obj.save()


@admin.register(models.Folder)
class FolderAdmin(ResourceAdminMixin, BaseAdmin):
    """Admin panel for `Folder` model."""
    autocomplete_fields = (
        'parent',
    )
    list_display = (
        'title',
        'parent',
        'owner',
        'matter',
        'is_shared',
        'is_template',
        'created',
        'modified',
    )
    search_fields = ('title',)
    list_filter = (
        'is_shared',
        'is_template',
    )
    autocomplete_list_filter = (
        'owner',
        'matter',
        'parent',
    )
    ordering = (
        'created',
        'modified'
    )
    fieldsets = (
        (_('Folder'), {
            'fields': (
                'parent',
                'path',
            )
        }),
        (_('Main info'), {
            'fields': (
                'title',
                'is_shared',
                'is_template',
            )
        }),
    )
    readonly_fields = (
        'path',
        'is_template',
    )
    related_models = (
        models.Folder,
        models.Document,
    )
    list_select_related = (
        'matter',
        'owner',
        'parent',
    )
    changelist_actions = [
        'open_templates_folder'
    ]

    def open_templates_folder(self, request, queryset):
        """ Перенаправьте администратора в корневую папку шаблона 
        администратора. """
        root_admin_template_folder = models.Folder.objects\
            .root_admin_template_folder()
        return redirect(
            'admin:documents_folder_change',
            object_id=root_admin_template_folder.pk
        )

    open_templates_folder.label = _('Open templates folder')
    open_templates_folder.short_description = _('Open templates folder')

    def has_change_permission(self, request, obj: models.Folder = None):
        """ Убедитесь, что администратор не пытается изменить 
        глобальную папку шаблона. """
        has_permission = super().has_change_permission(request, obj)
        if not obj:
            return has_permission
        return has_permission and not obj.is_root_global_template

    def has_delete_permission(self, request, obj: models.Folder = None):
        """ Убедитесь, что администратор не пытается удалить глобальную 
        папку шаблонов. """
        has_permission = super().has_delete_permission(request, obj)
        if not obj:
            return has_permission
        return has_permission and not obj.is_root_global_template
