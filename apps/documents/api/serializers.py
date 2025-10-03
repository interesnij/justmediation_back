from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.business.api.serializers.matter import ShortMatterSerializer
from apps.business.models import Matter
from apps.core.api.serializers import BaseSerializer
from apps.users.api.serializers import AppUserShortSerializer
from ...documents import models, utils
from ...users.api.serializers import AppUserWithoutTypeSerializer
from ...users.models import AppUser


class ResourceSerializer(BaseSerializer):
    """ Сериализатор для модели `Resource`. """
    matter_data = ShortMatterSerializer(
        source='matter', read_only=True
    )
    owner_data = AppUserWithoutTypeSerializer(
        source='owner', read_only=True
    )
    client_data = AppUserWithoutTypeSerializer(
        source='client', read_only=True
    )

    class Meta:
        model = models.Resource
        fields = (
            'id',
            'owner',
            'owner_data',
            'matter',
            'matter_data',
            'client',
            'client_data',
            'created',
            'modified',
            'parent',
            'title',
            'is_template',
            'is_vault',
            'is_global_template',
        )
        read_only_fields = (
            'owner',
            'is_global_template',
        )

    def get_fields(self):
        """ Ограничьте папки и материалы, к которым пользователь имеет доступ. """
        fields = super().get_fields()
        user = self.user
        if not user or not user.is_authenticated:
            return fields
        fields['parent'].queryset = models.Folder.objects.available_for_user(
            user=user
        ).exclude(is_template=True, owner__isnull=True)
        # Запретить перемещение ресурсов между папками matter
        # (из одной папки matter в папку другого вопроса)
        if self.instance and isinstance(self.instance, models.Resource):
            fields['parent'].queryset = fields['parent'].queryset.filter(
                matter=self.instance.matter
            )
        fields['matter'].queryset = Matter.objects.available_for_user(
            user=user
        )
        return fields

    def validate(self, attrs):
        """ Установите владельца ресурса. """
        attrs['owner'] = self.user
        is_template = attrs.get('is_template', False)
        is_vault = attrs.get('is_vault', False)
        matter = attrs.get('matter', None)
        client = attrs.get('client', None)
        if not is_template and not is_vault:
            if matter is None:
                raise ValidationError('Matter is required')
            if client is None:
                raise ValidationError('Client is required')
            if matter.client.user != client:
                raise ValidationError('Matter should be matched with client')
        return super().validate(attrs)


class DuplicateResourceSerializer(BaseSerializer):
    """ Сериализатор для дублирования модели `Resource`. """

    class Meta:
        fields = (
            'parent',
            'title'
        )
        extra_kwargs = {
            'parent': {
                'required': False,
            }
        }

    def get_fields(self):
        """ Ограничьте родителей. """
        fields = super().get_fields()
        if not self.user.is_authenticated:
            return fields
        fields['parent'].queryset = models.Folder.objects.available_for_user(
            self.user
        ).exclude(is_template=True, owner__isnull=True)
        return fields

    def validate(self, attrs):
        """ Проверьте, что у копии другой родительский элемент или заголовок. """
        parent = attrs.get('parent', self.instance.parent)
        title = attrs.get('title', self.instance.title)

        if title == self.instance.title and parent == self.instance.parent:
            if len(title.split('.')) > 1:
                filename = '.'.join(title.split('.')[:-1])
                extension = title.split('.')[-1]
            else:
                filename = '.'.join(title.split('.')[:-1])
                extension = ''
            count = type(self.instance).objects.filter(
                title__startswith=filename,
                title__endswith=extension,
                parent=parent,
            ).count()
            if len(title.split('.')) > 1:
                title = '.'.join(title.split('.')[:-1]) + f' ({count}).' + \
                    title.split('.')[-1]
            else:
                title = f"{title} ({count})"
            attrs['title'] = title

        return super().validate(attrs)

    def update(self, instance, validated_data):
        """Save copy."""
        instance.pk = None
        return super().update(instance, validated_data)


class DuplicateFolderSerializer(DuplicateResourceSerializer):
    """ Сериализатор для дублирования модели `Folder`. """

    class Meta(DuplicateResourceSerializer.Meta):
        model = models.Folder

    def update(self, instance, validated_data):
        """ Сохраните копию папки. """
        subfolders = instance.folders.all()
        documents = instance.documents.all()
        instance = super().update(instance, validated_data)
        utils.copy_folder_resources(instance, subfolders, documents)
        return instance


class DuplicateDocumentSerializer(DuplicateResourceSerializer):
    """ Сериализатор для дублирования модели `Document`. """

    class Meta(DuplicateResourceSerializer.Meta):
        model = models.Document
        fields = (
            'parent',
            'title'
        )
        extra_kwargs = {
            'title': {
                'required': False
            }
        }

    def update(self, instance, validated_data):
        """ Сохраните копию и установите created_by(тот, кто создал копию). """
        instance.created_by = self.user
        instance.is_template = False
        return super().update(instance, validated_data)


class FolderSerializer(ResourceSerializer):
    """ Сериализатор для модели `Folder`. """
    shared_with = serializers.PrimaryKeyRelatedField(
        queryset=AppUser.objects.all(),
        many=True,
        allow_empty=True,
        required=False
    )
    shared_with_data = AppUserShortSerializer(
        source='shared_with',
        many=True,
        read_only=True
    )

    class Meta:
        model = models.Folder
        fields = ResourceSerializer.Meta.fields + (
            'path',
            'is_shared',
            'shared_with',
            'shared_with_data',
            'type'
        )
        read_only_fields = ResourceSerializer.Meta.read_only_fields + (
            'path',
            'is_shared',
            'shared_with_data',
            'client_data'
        )
        relations = (
            'shared_with'
        )
        extra_kwargs = {
            'matter': {
                'required': False
            },
            'parent': {
                'required': False
            },
        }


class UpdateFolderSerializer(FolderSerializer):
    """ Обновить сериализатор для моедли `Folder`. """

    class Meta(FolderSerializer.Meta):
        read_only_fields = FolderSerializer.Meta.read_only_fields + (
            'matter',
        )

    def validate(self, attrs):
        """ Используйте метод проверки по умолчанию
        Мы используем метод проверки по умолчанию, чтобы ссылка на создателя
        не меняется при редактировании.
        """
        attrs['owner'] = self.user
        return super(BaseSerializer, self).validate(attrs)


class DocumentSerializer(ResourceSerializer):
    """ Сериализатор для модели `Document`. """
    created_by_data = AppUserWithoutTypeSerializer(
        source='created_by', read_only=True
    )
    #size = serializers.FloatField(source='file.size', read_only=True)
    size = 100
    shared_with = serializers.PrimaryKeyRelatedField(
        queryset=AppUser.objects.all(),
        many=True,
        allow_empty=True,
        required=False
    )
    shared_with_data = AppUserShortSerializer(
        source='shared_with',
        many=True,
        read_only=True
    )

    class Meta(ResourceSerializer.Meta):
        model = models.Document
        fields = ResourceSerializer.Meta.fields + (
            'file',
            'mime_type',
            'shared_with',
            'shared_with_data',
            'created_by',
            'created_by_data',
            #'size',
            'type'
        )
        read_only_fields = ResourceSerializer.Meta.read_only_fields + (
            'created_by',
            'mime_type',
            'shared_with_data',
            #'size',
        )
        relations = (
            'shared_with'
        )
        extra_kwargs = {
            'matter': {
                'required': False
            },
            'parent': {
                'required': False
            },
        }

    def validate(self, attrs):
        """ Установите создателя файла. """
        attrs = super().validate(attrs)
        attrs['created_by'] = self.user
        return attrs


class DocumentOverviewSerializer(BaseSerializer):
    """ Сериализует клиентские документы """
    uploaded_by = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )
    file_size = serializers.SerializerMethodField(
        read_only=True
    )
    shared_with_size = serializers.SerializerMethodField(
        read_only=True
    )

    def get_file_size(self, obj):
        """ Возвращает размер файла в килобайтах """
        return 100

    def get_shared_with_size(self, obj):
        """ Возвращает количество участников shared_with """
        return len(obj.shared_with.all())

    class Meta:
        model = models.Document
        fields = [
            'title',
            'created',
            'file_size',
            'shared_with_size',
            'uploaded_by'
        ]


class UpdateDocumentSerializer(DocumentSerializer):
    """ Обновить сериализатор для моедли `Document`. """

    def validate(self, attrs):
        """ Используйте метод проверки по умолчанию
        Мы используем метод проверки по умолчанию, чтобы ссылка на создателя
        не меняется при редактировании.
        """
        attrs = super().validate(attrs)
        title = self.instance.title
        if self.instance.owner != self.user:
            if len(title.split('.')) > 1:
                filename = '.'.join(title.split('.')[:-1])
                extension = title.split('.')[-1]
            else:
                filename = '.'.join(title.split('.')[:-1])
                extension = ''
            count = models.Document.objects.filter(
                title__startswith=filename,
                title__endswith=extension,
            ).count()
            if len(title.split('.')) > 1:
                title = '.'.join(title.split('.')[:-1]) + f' ({count}).' + \
                    title.split('.')[-1]
            else:
                title = f"{title} ({count})"
            attrs['title'] = title
        attrs['owner'] = self.user
        attrs['created_by'] = self.user
        return super(BaseSerializer, self).validate(attrs)

    def update(self, instance, validated_data):
        """ Сохраните копию. """
        if instance.owner != self.user:
            instance.pk = None
            instance.owner = self.user
            instance.created_by = self.user
        return super().update(instance, validated_data)


class CommonResourceSerializer(serializers.Serializer):
    """ Сериализатор для спецификаций swagger.
    Содержит все поля из FolderSerializer и DocumentSerializer.
    """

    id = serializers.IntegerField(required=False)
    owner = serializers.IntegerField(required=False)
    owner_data = AppUserWithoutTypeSerializer(required=True)
    matter_data = ShortMatterSerializer()
    title = serializers.CharField(required=True, max_length=255)
    path = serializers.ListField(required=False, allow_null=True)
    parent = serializers.IntegerField(required=False, allow_null=True)
    is_template = serializers.BooleanField()
    is_vault = serializers.BooleanField()
    type = serializers.ChoiceField(
        choices=[
            'Folder',
            'Document',
        ],
        required=True
    )
    mime_type = serializers.ReadOnlyField()
    created_by = serializers.IntegerField(required=False)
    created_by_data = AppUserShortSerializer(required=True)
    created = serializers.ReadOnlyField()
    modified = serializers.ReadOnlyField()


class DownloadFolderSerializer(BaseSerializer):
    """ Сериализует документы в папке. """
    size = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        #return ''
        return obj.file.split('/')[-1]

    def get_size(self, obj):
        #x = obj.file.size
        #y = 512000
        #if x < y:
        #    value = round(x/1000, 2)
        #    ext = 'KB'
        #elif x < y*1000:
        #    value = round(x/1000000, 2)
        #    ext = 'MB'
        #else:
        #    value = round(x/1000000000, 2)
        #    ext = 'GB'
        return str(10)+'KB'

        return str(value)+ext

    class Meta:
        model = models.Document
        fields = (
            'file',
            'size',
            'name'
        )
