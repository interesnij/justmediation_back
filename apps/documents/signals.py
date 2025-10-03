import mimetypes
from django.db.models import signals
from django.dispatch import Signal, receiver
from config.enums import RecordContractKind
from ..utils import eth
from . import models 


document_shared_by_mediator = Signal(providing_args=('instance',))
document_shared_by_mediator.__doc__ = (
    'Signal that indicates that document for client was shared'
)
document_uploaded_to_folder = Signal(providing_args=('instance',))
document_uploaded_to_folder.__doc__ = (
    'Signal that indicates that document was '
    'uploaded by someone in the folder.'
)
document_uploaded_to_matter = Signal(providing_args=('instance',))
document_uploaded_to_matter.__doc__ = (
    'Signal that indicates that document/folder was in the matter.'
)

# @receiver(signals.pre_save, sender=models.Folder)
# @receiver(signals.pre_save, sender=models.Document)
# def set_owner_for_resource(
#     instance: Union[models.Document, models.Folder], **kwargs
# ):
#     """Set resource's owner same as matter's mediator as parent's owner."""
#     if instance.parent_id:
#         instance.owner_id = instance.parent.owner_id
#     elif instance.matter_id:
#         instance.owner_id = instance.matter.mediator_id


# @receiver(signals.pre_save, sender=models.Folder)
# @receiver(signals.pre_save, sender=models.Document)
# def set_matter_for_resource(
#     instance: Union[models.Document, models.Folder], **kwargs
# ):
#     """Set resource's matter same as parent's(if it has one)."""
#     if instance.parent_id:
#         instance.matter_id = instance.parent.matter_id

# @receiver(signals.pre_save, sender=models.Folder)
# @receiver(signals.pre_save, sender=models.Document)
# def set_matter_for_resource(
#     instance: Union[models.Document, models.Folder], **kwargs
# ):
#     """Set resource's matter same as parent's(if it has one)."""
#     if instance.parent_id:
#         instance.matter_id = instance.parent.matter_id


@receiver(signals.pre_save, sender=models.Document)
def new_document_in_matter(instance: models.Document, **kwargs):
    """ Отправлять сигнал, когда документ загружается в matter """
    if instance.matter:
        document_uploaded_to_matter.send(
            sender=models.Document,
            instance=instance
        )


@receiver(signals.pre_save, sender=models.Document)
def set_document_mine_type(instance: models.Document, **kwargs):
    """Set document mime_type."""
    if not instance._state.adding:
        return
    instance.mime_type = mimetypes.guess_type(str(instance.file))[0]


@receiver(signals.post_save, sender=models.Document)
def new_shared_file(
    instance: models.Document, created: bool, **kwargs
):
    """ Отправьте сигнал о том, что адвокат поделился документом. """
    if not created:
        return

    if instance.created_by_id != instance.owner_id:
        document_uploaded_to_folder.send(
            sender=models.Document,
            instance=instance
        )

    is_new_shared_file_by_mediator = (
        instance.is_shared_folder_document and
        instance.created_by.is_mediator
    )
    if is_new_shared_file_by_mediator:
        document_shared_by_mediator.send(
            sender=models.Document,
            instance=instance
        )


@receiver(signals.post_save, sender=models.Document)
def save_to_contract(
    instance: models.Document, created: bool, **kwargs
):
    if not created:
        return

    import hashlib, pathlib
    from urllib.request import urlopen
    file = urlopen(instance.file)
    md5 = hashlib.md5(file.read()).hexdigest()

    instance.md5 = md5
    transaction_id = eth.create_new_record(md5, RecordContractKind.DOCUMENT)
    instance.transaction_id = transaction_id
    if not instance.title:
        instance.title = instance.file.split("/")[-1]
    if not instance.mime_type:
        instance.mime_type = instance.file.split(".")[-1]
    instance.save()
    
