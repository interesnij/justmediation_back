from config.celery import app

from .services import resync


@app.task()
def firebase_resync():
    """Re-sync firebase chats with backend database."""
    resync.sync_chats()
