from django.db.models import Model
from apps.documents.models import Document
from ...models import Matter


def is_created(instance: Model, created: bool = None, **kwargs) -> bool:
    """ экземпляр создан? """
    # используйте "создано" из сигнала, если он был установлен
    if created is not None:
        return created
    return instance._state.adding


def is_not_created(instance: Model, created: bool = None, **kwargs) -> bool:
    """ экземпляр не создан? """
    return not is_created(instance, created, **kwargs)


def is_shared_folder_document(instance: Document, **kwargs) -> bool:
    return instance.is_shared_folder_document


def is_not_open(instance: Matter, **kwargs) -> bool:
    return not instance.is_open
