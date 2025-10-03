from django.db.models import Q, QuerySet
from apps.users.models import AppUser


class ResourceQuerySet(QuerySet):
    """QuerySet for `Resource` model."""

    def root_resources(self):
        """ Получите корневые ресурсы. """
        return self.filter(parent=None)

    def available_for_user(self, user: AppUser):
        """ Получить ресурсы, которыми владеет пользователь. """
        from apps.business.models import Matter

        available_matters = Matter.objects.all().available_for_user(user) \
            .values('id')
        if user.is_mediator:
            qs = self.filter(
                Q(owner=user) |
                Q(matter_id__in=available_matters) |
                Q(is_template=True, owner=None)
            )
        elif user.is_client:
            qs = self.filter(
                Q(owner=user) |
                Q(matter_id__in=available_matters)
            )
        else:
            qs = self.filter(
                Q(owner=user) |
                Q(matter_id__in=available_matters) |
                Q(is_template=True, owner=None)
            )
        # matter__shared_links создает дубликаты
        # Он генерирует `правильное соединение`
        return qs.distinct()

    def private_resources(self, user: AppUser):
        """ Получить личные ресурсы пользователя.
        Частные ресурсы - это ресурсы, которые принадлежат пользователю, а не
        связанный с чем-либо (например, с делом).
        """
        return self.available_for_user(user).filter(matter=None).exclude(
            is_template=True, owner=None
        )

    def global_templates(self):
        """ Получите ресурсы, которые являются шаблонами администратора """
        return self.filter(
            is_template=True, owner=None
        )

class FolderQuerySet(ResourceQuerySet):
    """QuerySet for `Folder` model."""

    def available_for_user(self, user: AppUser):
        """ Получить ресурсы, которыми владеет пользователь. """
        qs = super().available_for_user(user)
        # Показывать общие папки только для клиента
        return qs

    def root_admin_template_folder(self):
        """ Получите корневую папку шаблона администратора. """
        return self.get(
            is_template=True, owner__isnull=True, parent__isnull=True
        )


class DocumentQuerySet(ResourceQuerySet):
    """QuerySet for `Document` model."""

    def available_for_user(self, user: AppUser):
        """ Получить ресурсы, которыми владеет пользователь. """
        qs = super().available_for_user(user)
        # Показывать документы в общих папках только для клиента
        return qs
