class ActionPermissionsMixin(object):
    """ Mixin, который позволяет определять конкретные разрешения для каждого действия
    Для этого требуется заполненный атрибут `permissions_map`
    Он должен использоваться для `ModelViewSet`
    Примеры:
        class NoteViewSet(ActionPermissionsMixin, viewsets.ModelViewSet):
            queryset = Note.objects.all()
            serializer_class = NoteSerializer
            base_permission_classes = [IsAuthenticated, IsConferenceAttendee]
            permissions_map = {
                'list': base_permission_classes + [IsOwner],
                'update': base_permission_classes + [CanModerate, IsOwner],
                # разрешения по умолчанию для всех других действий
                # если раздел "по умолчанию" не определен
                'default': base_permission_classes + [CanModerate],
            }
    """

    permissions_map = None

    def get_permissions(self):
        """ Возвращает список разрешений для текущего значения атрибута `.action`.
        Он возвращает список разрешений из `permissions_map`, используя действие view
        как ключ. Если у view нет permissions_map или permissions_map не
        имеет ключа `default`, мы используем `get_view set_permissions`, если у view есть это
        attr, или иначе мы используем `super().get_permissions()`.

        Возвращается:
            список: список разрешений для связанных действий
        """
        permissions = super().get_permissions()
        if hasattr(self, 'get_viewset_permissions'):
            permissions = self.get_viewset_permissions()

        # если действие отсутствует в permission_map - добавить представление
        # `base_permission_classes` и дополнительные из `permission_classes`
        # по умолчанию
        is_permissions_map_set = isinstance(self.permissions_map, dict)

        if not is_permissions_map_set:
            return permissions

        if self.action in self.permissions_map:
            return self.get_permissions_from_map(self.action)

        if 'default' in self.permissions_map:
            return self.get_permissions_from_map('default')

        return permissions

    def get_permissions_from_map(self, action):
        """ Верните список разрешений из карты разрешений. """
        return [p() for p in self.permissions_map[action]]


class ActionSerializerMixin(object):
    """ Mixin, который позволяет определять конкретные сериализаторы для каждого действия.
    Для этого требуется заполненный атрибут `serializers_map`
    Он должен использоваться для `ModelViewSet`

    Примеры:
        class NoteViewSet(ActionSerializerMixin, viewsets.ModelViewSet):
            queryset = Note.objects.all()
            serializer_class = NoteSerializer
            serializers_map = {
                'update': serializers.UpdateNoteSerializer,
                'partial_update': serializers.UpdateNoteSerializer,
            }
    """
    serializers_map = None

    def get_serializer_class(self):
        """ Получите сериализатор для действия view.
        Сначала мы пытаемся найти соответствующее "действие" в "serializer_map", и
        в случае, если текущий метод отсутствует в "serializer_map", мы возвращаем
        `default` из `serializer_map`(если значение по умолчанию не задано, мы используем
        serializer_class из `super().get_serializer_class()`).

        Пример:
            serializer_map = {
                'update': serializers.UpdateLeadSerializer,
                'partial_update': serializers.UpdateLeadSerializer,
            }

        """
        serializer_class = super().get_serializer_class()
        is_serializers_map_set = isinstance(self.serializers_map, dict)

        if not is_serializers_map_set:
            return serializer_class

        if self.action in self.serializers_map:
            return self.serializers_map.get(self.action)

        if 'default' in self.serializers_map:
            return self.serializers_map.get('default')

        return serializer_class
