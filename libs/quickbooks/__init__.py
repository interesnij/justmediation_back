from django.conf import settings
from .clients import QuickBooksClient, QuickBooksTestClient


default_quickbooks_client = (
    QuickBooksClient
)
