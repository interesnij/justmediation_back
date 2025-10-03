import factory
from ..documents import models


class DocumentFactory(factory.DjangoModelFactory):
    """Generate test `Document` model."""
    mime_type = factory.Faker('mime_type')
    title = factory.Faker('ean13')
    file = factory.django.ImageField(color='magenta')
    parent = factory.SubFactory('apps.documents.factories.FolderFactory')
    created_by = factory.SubFactory('apps.users.factories.AppUserFactory')
    owner = factory.SubFactory('apps.users.factories.AppUserFactory')

    class Meta:
        model = models.Document


class FolderFactory(factory.DjangoModelFactory):
    """Generate test `Folder` model."""
    title = factory.Faker('ean13')
    is_shared = False
    owner = factory.SubFactory('apps.users.factories.AppUserFactory')

    class Meta:
        model = models.Folder

    @factory.post_generation
    def files(self: models.Folder, *args, **kwargs):
        document_generation_params = {
            'size': 2,
            'owner': self.owner,
            'parent': self,
        }
        if self.is_template:
            self.documents.set(
                DocumentFactory.create_batch(
                    is_template=True,
                    **document_generation_params
                )
            )
        elif self.owner:
            self.documents.set(
                DocumentFactory.create_batch(
                    created_by=self.owner,
                    **document_generation_params
                )
            )
        elif self.matter:
            del document_generation_params['size']
            self.documents.set(
                (
                    DocumentFactory(
                        created_by=self.matter.client.user,
                        **document_generation_params
                    ),
                    DocumentFactory(
                        created_by=self.matter.mediator.user,
                        **document_generation_params
                    )
                )
            )


class PrivateFolderFactory(FolderFactory):
    """Generate private folder."""
    owner = factory.SubFactory('apps.users.factories.AppUserFactory')


class MatterFolderFactory(FolderFactory):
    """Generate matter related folder."""
    matter = factory.SubFactory('apps.business.factories.MatterFactory')
