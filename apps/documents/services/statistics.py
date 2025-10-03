from ...users import models as user_models


def get_mediator_statistics(mediator: user_models.Mediator) -> dict:
    """ Получите статистику адвоката для приложения documents. """
    documents_count = mediator.user.documents.count()

    return {
        'documents_count': documents_count,
    }
