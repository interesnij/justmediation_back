from rest_framework import permissions


class IsNotSharedFolder(permissions.BasePermission):
    """ Проверьте, является ли папка общей или нет. """

    def has_object_permission(self, request, view, obj):
        """ Запретите операцию, если это общая папка. """
        return not (not obj.is_template and obj.is_shared)


class IsNotAdminTemplate(permissions.BasePermission):
    """ Проверьте, не является ли папка шаблоном администратора. """

    def has_object_permission(self, request, view, obj):
        """ Запретить операцию, если это ресурс шаблона администратора. """
        return not obj.is_global_template


class IsNotPersonalRootTemplateFolder(permissions.BasePermission):
    """ Проверьте, не является ли папка корневой папкой шаблона адвоката. """

    def has_object_permission(self, request, view, obj):
        """ Запретить операцию, если это корневая папка шаблона адвоката. """
        return not obj.is_root_personal_template
