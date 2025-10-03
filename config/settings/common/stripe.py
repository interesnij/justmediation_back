STRIPE_WEBHOOK_VERSION = '2019-10-08'

# способ проверки веб-ссылок, поступающих в приложение (по соображениям безопасности)
# всегда должно быть `verify_signature`, потому что проверка `retrieve_event`
# не будет работать для stripe connect API (события stripe connect не могут быть
# найдено во всех API событий webhooks, они подключены к `подключенным учетным записям`)
DJSTRIPE_WEBHOOK_VALIDATION = 'verify_signature'
DJSTRIPE_WEBHOOK_SECRET = None
DJSTRIPE_WEBHOOK_URL = r"webhook/$"
 