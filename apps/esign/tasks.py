from config.celery import app

from .models import Envelope
from .services import clean_up_removed_in_docusign_envelopes_from_db


@app.task()
def clean_old_envelopes():
    """Celery task to clean old envelopes from DB.

    Currently there is a problem in DocuSign that it removes all envelopes for
    `demo` accounts after 30 days and only `draft` envelopes in production
    after 30 days too without any notifications and webhooks.

    https://support.docusign.com/articles/How-long-does-DocuSign-store-my-documents

    So the fix is:

        - delete all envelopes older 30 days and move matter to `Draft` status
        for `development` and `staging`

        - delete only `draft` envelopes older 30 days for `production`

    """
    envelopes = Envelope.objects.all().old_envelopes()
    for envelope in envelopes:
        clean_up_removed_in_docusign_envelopes_from_db(envelope)
