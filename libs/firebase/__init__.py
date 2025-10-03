from django.conf import settings
from .clients import FirestoreClient, FirestoreTestClient


default_firestore_client = (
    FirestoreClient() if not settings.TESTING and settings.FIREBASE_ENABLED
    else FirestoreTestClient()
)
