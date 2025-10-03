import mimetypes
import uuid
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from . import querysets
from ...users.models.users import AppUser

__all__ = (
    'Resource',
    'Folder',
    'Document',
)

def upload_documents_to(instance, filename: str) -> str:
    """ Загрузите экземпляры "документы" в папку "документы" или "шаблоны".
    Аргументы:
        instance (Document): экземпляр модели документа
        filename (str): имя файла документа.
    Возвращается:
        str: Сгенерированный путь к файлу документа.
    """
    document_path = f'{uuid.uuid4()}/{filename}'

    if getattr(instance, 'is_global_template', None):
        return f'public/templates/{document_path}'
    return f'documents/{document_path}'

class Resource(BaseModel):
    """ Общая модель для ресурсов.
    Атрибуты:
        owner (AppUser):
            если это личная папка, когда это сам пользователь
            если это папка, связанная с делом, когда это дело адвоката
        matter (Matter): отношение к делу
        parent (Folder): показывает, находится ли ресурс внутри другой папки
        title (str): Название ресурса
        is_template (book): Является шаблонным ресурсом
    """
    owner = models.ForeignKey(
        AppUser,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    matter = models.ForeignKey(
        'business.Matter',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Matter'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    client = models.ForeignKey(
        AppUser,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('client'),
        related_name='%(class)s',
        related_query_name="%(app_label)s_%(class)s",
    )

    parent = models.ForeignKey(
        'documents.Folder',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Parent'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title of resource')
    )

    is_template = models.BooleanField(
        default=False,
        verbose_name=_('Is a template'),
        help_text=_('Is a template')
    )

    seen = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('Seen'),
    )

    is_vault = models.BooleanField(
        default=False,
        verbose_name=_('Is in vault'),
        help_text=_('Is in vault')
    )

    objects = querysets.ResourceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = ['parent', 'title','owner', 'matter']
        # Ответ на вопрос, почему нет общих ограничений, из django docs
        # Вы всегда должны указывать уникальное имя для ограничения. Как таковой,
        # обычно вы не можете указать ограничение для абстрактного базового 
        # класса, поскольку параметр Meta.constraints наследуется подклассами, с
        # точно такие же значения для атрибутов (включая имя) каждого время.
        # Вместо этого укажите параметр constraints непосредственно для 
        # подклассов, предоставив уникальное имя для каждого ограничения.

    def __str__(self):
        model_name = self._meta.verbose_name
        return f"{model_name}: '{self.title}'"

    @property
    def is_global_template(self) -> bool:
        """ Проверьте, является ли ресурс ресурсом шаблона администратора. """
        return (
            self.is_template and self.owner_id is None
        )

    @property
    def is_root_global_template(self) -> bool:
        """ Проверьте, является ли ресурс шаблоном корневого администратора. """
        return (
            self.is_global_template and self.parent_id is None
        )

    @property
    def is_personal_template(self) -> bool:
        """ Проверьте, является ли ресурс персональным шаблонным ресурсом. """
        return self.is_template and self.owner_id

    @property
    def is_root_personal_template(self) -> bool:
        """ Проверьте, является ли ресурс корневым персональным шаблонным ресурсом. """
        return (
            self.is_personal_template and self.parent_id is None
        )

    def clean_matter(self):
        """ Убедитесь, что мы не пытаемся создать шаблон в matter. """
        if not self.matter_id:
            return

        if self.is_template:
            raise ValidationError(
                f'Template {self.__class__.__name__.lower()} can not be '
                f'placed in matter'
            )

    def clean_parent(self):
        """ Проверьте parent.
        Проверьте, что ресурс не является родительским по отношению к самому 
        себе. Проверьте, что ресурс не является дочерним по отношению к 
        своему дочернему элементу.
        """
        if not self.parent_id or not self.parent.parent_id:
            return

        if self.id == self.parent_id:
            raise ValidationError("Resource can't be parent to itself")

        if isinstance(self, Folder) and self.pk in self.parent.path:
            raise ValidationError("Parent can't become child")

        # Ресурсы шаблона не могут иметь значения.
        if not self.is_template:
            return

        if self.parent_id and self.parent.matter_id:
            raise ValidationError(
                f'Template {self.__class__.__name__.lower()} can not be '
                f'placed in matter'
            )

    def clean_title(self):
        """ Проверьте, что ресурс уникален по имени в корневой папке.
        unique_together не улавливает случаи, когда parent равен null. 
        """
        owner_id = self.matter.mediator_id if self.matter_id else self.owner_id
        duplicate = self.__class__.objects.filter(
            title=self.title,
            parent_id=self.parent_id,
            matter_id=self.matter_id,
            owner_id=owner_id
        ).exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError(
                f'You are trying to upload a duplicate '
                f'{self.__class__.__name__.lower()}. '
                'Please try again.'
            )


class Folder(Resource):
    """ Модель представляет собой файловую папку.
    Атрибуты:
        owner (AppUser):
            если это личная папка, когда это сам пользователь
            если это папка, связанная с делом, когда это дело адвоката`
        matter (Matter): отношение к материи
        parent (Folder): показывает, находится ли папка внутри другой папки
        title (str): Название папки
        path (list[int]):
            путь к иерархии папок. Учить больше:
            http://www.monkeyandcrow.com/blog/hierarchies_with_postgres/
        is_shared (bool):
            Является ли папка общей для клиента matter? если используется общий доступ, папка
            виден как клиенту, так и адвокату, клиент имеет доступ к
            файлам только в папке этого вопроса.
            Общая папка должна быть создана при создании материала.
    """

    path = ArrayField(
        models.IntegerField(),
        default=list,
        verbose_name=_('Path'),
        help_text=_('Materialized path of folder hierarchy')
    )

    is_shared = models.BooleanField(
        default=False,
        verbose_name=_('Is shared'),
        help_text=_(
            'Is folder shared between mediator and client'
        )
    )

    shared_with = models.ManyToManyField(
        AppUser,
        related_name='shared_folder',
        verbose_name=_('Shared with'),
        help_text=_('Users with which folder is shared')
    )

    objects = querysets.FolderQuerySet.as_manager()

    class Meta(Resource.Meta):
        abstract = False
        verbose_name = _('Folder')
        verbose_name_plural = _('Folders')
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'parent'],
                condition=models.Q(matter__isnull=True),
                name='unique private root folder'
            ),
            models.UniqueConstraint(
                fields=['title', 'matter'],
                condition=models.Q(parent__isnull=True),
                name='unique matter root folder'
            ),
            models.UniqueConstraint(
                fields=['title', 'owner'],
                condition=models.Q(parent__isnull=True, matter__isnull=True),
                name='unique root folder'
            ),
            models.UniqueConstraint(
                fields=['matter', 'is_shared'],
                condition=models.Q(is_shared=True, matter__isnull=False),
                name='unique shared folder for matter'
            ),
            models.UniqueConstraint(
                fields=['is_template'],
                condition=models.Q(
                    owner__isnull=True, parent__isnull=True, is_template=True
                ),
                name='unique root template folder'
            ),
            models.CheckConstraint(
                check=~models.Q(pk=models.F('parent')),
                name="parent can become parent to itself"
            ),
            models.CheckConstraint(
                check=(
                    models.Q(is_shared=True, matter__isnull=False) |
                    models.Q(is_shared=False)
                ),
                name="shared folder must have matter"
            ),
        ]

    @property
    def shared_with_users(self):
        """ Пользователи, которые поделились с """
        return [self.matter.client.user] if self.is_shared else []

    @property
    def type(self) -> str:
        """Return type"""
        return 'Folder'

    def clean_parent(self):
        """ Убедитесь, что родительская папка не является общей папкой. """
        super().clean_parent()
        if not self.parent_id:
            return

        if self.parent.is_shared and self.parent.matter_id:
            raise ValidationError(
                "Matter shared folder can't contain sub-folders"
            )

    def clean_is_shared(self):
        """ Убедитесь, что мы не создаем дополнительную общую папку для matter.
        Также убедитесь, что мы не пытаемся создать общую папку шаблона.
        """
        if not self.is_shared:
            return
        if self.is_template:
            raise ValidationError(
                'Shared folder can not be template folder'
            )
        if not self.matter_id:
            raise ValidationError(
                'Shared folder can be only created for matters'
            )
        if self.matter_id:
            duplicate = self.__class__.objects.filter(
                is_shared=True, matter_id=self.matter_id
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError(
                    'There are can be only one shared folder per matter'
                )

    def update_path(self):
        """ Обновите поле пути для себя и дочерних элементов. """
        if not self.parent_id:
            self.path = [self.pk]
        else:
            self.path = self.parent.path + [self.pk]

    def save(self, **kwargs):
        """ Обновите поле пути для папки и ее вложенных папок. """
        super().save(**kwargs)
        self.update_path()
        super().save()
        # ЗАДАЧА найти лучшее решение для обновления путей к вложенным папкам
        for folder in self.folders.all():
            folder.save()


class Document(Resource):
    """ Модель представляет собой документ (файл) в библиотеке.
    В этой модели хранятся простые данные о файле, хранящемся в приложении, 
    такие как название, ссылка на хранилище, автор и т.д.

    Атрибуты:
        owner (AppUser):
            если это личная папка, когда это сам пользователь
            если это папка, связанная с делом, когда это дело адвоката`
        matter (Matter): отношение к материи
        parent (Folder): папка, в которой хранится документ.
        created_by (AppUser): Ссылка на автора документа
        mime_type (str): Mime-тип файла
        file (str): файл документа в хранилище
        title (str): Название документа
    """

    created_by = models.ForeignKey(
        AppUser,
        on_delete=models.PROTECT,
        verbose_name=_('Created by'),
        related_name='created_documents',
    )

    mime_type = models.CharField(
        max_length=255,
        verbose_name=_('Mime type'),
        help_text=_('Mime type of file')
    )
    file = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        #editable=False,
        verbose_name=_('File'),
        help_text=_("Document's file")
    )

    shared_with = models.ManyToManyField(
        AppUser,
        related_name='file',
        verbose_name=_('Shared with'),
        help_text=_('Users with which document is shared')
    )

    transaction_id = models.CharField(
        blank=True,
        help_text='Transaction ID',
        max_length=128,
        null=True,
        verbose_name='Transaction ID'
    )

    md5 = models.CharField(
        blank=True,
        help_text='Transaction ID',
        max_length=100,
        null=True,
        verbose_name='md5sum'
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        verbose_name='uuid'
    )

    objects = querysets.DocumentQuerySet.as_manager()

    class Meta(Resource.Meta):
        abstract = False
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'parent'],
                condition=models.Q(matter__isnull=True),
                name='unique private root document'
            ),
            #models.UniqueConstraint(
            #    fields=['title', 'matter'],
            #    condition=models.Q(parent__isnull=True),
            #    name='unique matter root document'
            #),
            models.UniqueConstraint(
                fields=['title', 'owner'],
                condition=models.Q(parent__isnull=True, matter__isnull=True),
                name='unique root document'
            ),
        ]

    @property
    def is_shared_folder_document(self) -> bool:
        """ Проверьте, принадлежит ли документ к `shared_folder`. """
        if not self.parent_id:
            return False
        return self.parent.is_shared

    @property
    def type(self) -> str:
        """Return type"""
        return 'Document'

    def clean(self):
        """ Убедитесь, что файл имеет mime-тип. """
        super().clean()
        mime_type = mimetypes.guess_type(str(self.file))[0]
        if not mime_type:
            raise ValidationError(
                "Failed to determine mime type of file. File probably doesn't "
                "have an extension."
            )
    
    def save(self,*args,**kwargs):
        self.uuid = uuid.uuid4().hex
        super().save()

    @classmethod
    def client_documents(cls, client):
        """
        Извлекает и возвращает набор запросов к документу
        для документов, связанных с клиентом
        """
        # личные документы клиента
        documents = cls.objects.filter(owner=client.user)

        # добавление документов, связанных с вопросами клиента
        documents |= cls.objects.filter(matter__in=client.matters.all())

        return documents
