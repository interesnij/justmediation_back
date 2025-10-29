from .common import *

DEBUG = True
ENVIRONMENT = 'production'
 
BASE_URL = 'https://backend.justmediationhub.com'

ADMINS = (
    'interesnijsim49293@gmail.com',
    'zuvarevserg@outlook.com',
    'support@justmediationhub.com',
    'alex.goldobin@justmediationhub.com'
)
MANAGERS = ADMINS
MAINTAINERS = ADMINS

SECRET_KEY = 'nyk@yat92830fe+2a(v5kx6*!h$d0oa5x!n^xvwpb+f5#v6+-i'

OUT_TOKEN = 'key_BUVEnKnbfbddfdf_gggg_fbfbf_XXBcLGdyg3ZdsO6JCPG5kh947MPjy'
#F_DOMAIN = 'https://t.juslaw.online/'
F_DOMAIN = ''

SALT = 'aZ!!12Qe'
ALLOWED_HOSTS = ['*']  

DATABASES = { 
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'db2', 
        'USER': 'serg',
        'PASSWORD': 'ulihos46',
        'HOST': 'localhost',
        'PORT': '5432',
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'connect_timeout': 30,
        },
    }
}

PROD_FRONTEND_LINK=(
        'https://app.justmediationhub.com/',
        'Prod frontend url',
        'url_field'
    )


EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = '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'
EMAIL_BACKEND = 'sgbackend.SendGridBackend' 

SENDGRID_API_KEY = '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' 
SENDGRID_SANDBOX_MODE_IN_DEBUG=False
SENDGRID_ECHO_TO_STDOUT=False 

"""
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'justmediationhub.com@gmail.com'
EMAIL_HOST_PASSWORD = 'vrevfnsdhjyhmdsr'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'Beatrice@jusglobal.com'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
"""

ETH_PRIVATE_KEY = 'ac1fa63ad312480edab133a5ebb6ecc266aa582efa7cc6e183397bdca07a508b'
ETH_CONTRACT_ADDRESS = '0xF0A3599C2bC7b9a0D4cC776191cB6c9eb215fCb0'
ETH_NETWORK_NAME = 'polygon'
WEB3_INFURA_PROJECT_ID = '22e4b7ccdada4106b1db72af745497fb'

CELERY_TASK_DEFAULT_QUEUE = 'celery'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'

CACHEOPS_REDIS = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 1,
    'socket_timeout': 3
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'MAX_ENTRIES': 1000,
        },
    }
}

firestore_config = {
  "type": "service_account",
  "project_id": "continual-tine-224909",
  "private_key_id": "1aa3387d9097539225d73f0fd186b0173e9b3d47",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDXoNoF+pRLDM4R\nKbWO9bq0L0MIL8HCpi4DhBSzxj9PMjz3dhJwSDSLF6k95pfnu7xpjSudmpFVMGeX\nCHAaFoh5iYndLUs+Uc69ivGlwHsw0aQQrm+NjUI/xmlD254mNLsDch4L9F2q/n5W\nIuE1uBs4ujsQbxUP8AbJpnAgNhzTCVdcTfcH/ASnBgY7ytDBeROKpLJilojzDyVa\n2LozDW2hlNXMWaZ1aGrZla5oXbfDF73vltSwk/SUZfqQqcbg2nerphDYmypeSl2e\nY4r3f6L3OZFqEE++gbZjKRTFnCOiKibcqCP4JphKMAFQZ2xG01zkMtBuEG9s1dIy\nKRaelGthAgMBAAECggEAUiwTSfn/L0aW9QVvEibk2qu0INeKQHJx0JcyCHyBPd4I\nS8msJyvtEiCXN2a79uydVaAdwfbYcZ17rJvjlJ2HrsFST35mUT59yc+8XQ0oJSeP\nHWhMTKZLW+Bx1xFHiInJxvtjJe0fEP3hCVRLfNxHS2v0/ENIxIUVIR2TV0Mn4ufW\nBMxkg0mOLwsCjbBc9TJ/IqQ4JLb4p8rZhEFnQAp+97tFkgDPhofVDz99cdLA13dd\nqq2Wh8v2pWFJr0IB4SrHl4kKAmBgCE6A2/OCvGUAoIQc4+Wc3o59QIkdkwuM/6Sn\nToQqczevdGM58O43IgNTecoIrpC1rhA749TTvSacLQKBgQD5fBhMH9zE9KUETlji\ninXYiT3+e41rjUumHxxkvoGNVtrxIonWi0LgrOgVlkb1AS42hwzuRvauXMNPDtgO\nGCq8H1VCou3lfjYpPVM9srrb400Lob1ei2QwTvHPZxwRnHlsCB4dYnCPGQYEI26A\nY3LywBy7kCBKJwzMvutl/Ae7WwKBgQDdQmm+9aGWDywmsCD/iDXfoiG4hAmaYZjN\nMhdMsm4EXtWttXufFtWFLoxbyZbkcAK2YoJIL41Hg/1/K09t8e/cUz78KEP8ClCR\nDqh68djJMb6biI/xnkHsoeleMY/YV5KqlPO3Zc9t2+fcecve9dUmUvnWVZMxncD3\nDuI4nXD88wKBgHY2O5kOW+Ai/3Gr4eftrWsdlHdZeaflelvLT/vYXLBo4DLzp5Y1\nxEmLBCj+XL7IgWoq0ZCxpT73C0ARi4QaJV2gBxkc9FYSWH1v5lpMrsdzy1TgnUcI\nCz/smB0rARzDJLFwozxPIYBcXgJl+3zwIk4tgy/IWdRo7mKxb/6RzeQTAoGBAMib\nmn0FAEip4QIC1yhYO2BUA/bj4EEVFBGXxQBJFu7nfR1OWpNXhKiIF8Jw+FqOJCdx\nEWaZlqKszX4rqoyouy0sXQMLDvjJ8VpTy/YMqN1iOMuT+c68ClGeS5SXozAn1lbL\nTl2N9ZBJveNsmqfAhE2HFfZ7CEYIHhjiacGjHfp5AoGALctIJMvlaFxzkW3mI1xf\n5IekNOana3lxZqZhqp81oJWoNHB4GVOkEUKhdbSPLjRFDJSURHBGfA1ouHvNhSyC\nPthQdjuk+P1yLgBY0NeRJC1Q5AOzcEAXUdhunJ/AuGT7b5t1ETI4Qkk2PO9ZC8o7\nuxu1ZETugu2X71s5zuhtqcQ=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-c9jhq@continual-tine-224909.iam.gserviceaccount.com",
  "client_id": "112247693818316605976",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-c9jhq%40continual-tine-224909.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

STRIPE_ENABLED = True
STRIPE_LIVE_MODE = True
STRIPE_LIVE_PUBLIC_KEY = 'pk_live_8kHQq7Esqylmfjj1UqQma3yY'
STRIPE_LIVE_SECRET_KEY = 'sk_live_88179d4Pr6jxBzr0pRkvEgf7'
DJSTRIPE_WEBHOOK_SECRET = 'whsec_svX4wfORabtiyZiSD3HumqB1fXaGJE8m'

STRIPE_CONNECT_CLIENT_ID = 'ca_HuTdaerbRKso1a32vRy4O6LPggLdH0L1'
STRIPE_BASE_AUTH_ERROR_REDIRECT_URL = 'https://app.jus-law.com/dashboard'
DJSTRIPE_CONNECT_WEBHOOK_SECRET = 'whsec_xTXhYIX1MsXO351Oo8VkS0HUrxY7bGk7'

AWS_STORAGE_BUCKET_NAME = 'juslaw-development-uploads'
AWS_S3_DIRECT_REGION = 'us-east-1'
AWS_S3_ENDPOINT_URL = 'https://s3.%s.amazonaws.com' % AWS_S3_DIRECT_REGION
AWS_USE_SSL = 'true'
AWS_ACCESS_KEY_ID = 'AKIAZWC25L2HZU3CHZRW'
AWS_SECRET_ACCESS_KEY = "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"

DOCUSIGN['BASE_PATH'] = 'docusign.com'
DOCUSIGN['OAUTH_HOST_NAME'] = 'account.docusign.com'
DOCUSIGN['PRIVATE_RSA_KEY'] = '-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEAx4VdUHR31mckFPr2+YqH/Xxx5phbRfJdV0kPJNx7doHQsIdU\\nOknxWUAWQj4tl4z4MLr7Vs/UWvAiR4btWJwFVC59RRl8szxc7dAIAgXjnE/6UESC\\nAP2LJOxjpJby2p2OGycwi/Pwr9HZ6PPQbOYpW0BXMfmexB3KTgJXVLOaulOMAlzv\\nQ/vQ6LZPDH2WGyxGWNFOM+GlVb6in4JjovDbhbBiEX5+dyOIRC4MoGeyDjSMGOxP\\n8o44giC29mg1TGLyxoOj2VozDjE8pb+fKdzgVUhnAT0YQoXylp+4NxHhOjUjzeoL\\nT0+zoCRhyeXxoqsmw4ieXru45sYOi4+OxUfyawIDAQABAoIBAAigQgxXbLlVR9Pf\\nlP8ghFUEpO80r3i5S/XMT9GAXGO5CxFTi7DiP4Mw6FJAc+71OXzwQiuOD37hZ1Bm\\nWF6YKD044VIA3xZOSf1yHNaEwKlvMvUQPfqi+5NC5EmNlfEdSYAjbc+vLtaH7eVK\\nnTxudJbgYKSyR33wUWD8BiCNJbRgEsM4kAPd72EUOwHKPJAFHXiL3DQO2830qN39\\nb+IvY5Y/D0n4VyltJhUnhBsTVevgwA+Rj68MnUGWhLbbKKvX9GLQg6n8sBmENcr9\\nQXtDfHh1IDKJ6psDi+NuR2UJTs5nxG+XzU7KRGztGJN98y3KZzBmaVfAd4lk1ma5\\nW6rWRZkCgYEA6ugDJeC8EWp5A1wwEtYuSoFqjYKNePPjbqgr4bh+IF32j8o8CZYF\\nWxsLAsZap8RI1uz7gfoE9qFqNTDIN8jZgilGXMdnY1XdOp70LC7/3sajlCvSQtdp\\nWa4Zi8OOt3g7q7u7YcKFQCaAh78iS+tBIvdPEfse6ZPI5WZODMe5I20CgYEA2W/r\\ncm5wXuOFliwLF1TQh3IpFXL7LBLiRDBNwT/uemN2LCy63TzQX9/Titr8ofyOTv4B\\nGWBuROCSFhgb0EiytaCAQbGxbPv5EahD6qE4W1EY4h19KW7SB9M0S6FBuioK/ky+\\nhyCEQ+ECKzI8dUH1rlNaeja+Um+PZypyGWaa7jcCgYEAnToHiV2/Y0TJlIcqoiD7\\nQOEYSXkdadyL2G/1VxJeURmzQxDQWHYyRYV3PDc5TFsjib96o8eNdOobJVjuWfA0\\nLVuk/cp1l9ZLycXElqIqnpiDulQOWrDFkcHm1VZh+skd31c7FzbUa1iZ5MH4manv\\nohC3ushDK4HAEFMGYKV5dI0CgYAQeQcoWy+OMMR9FQceFGHb8Q0lv9lBhIi5y8MI\\nQfSqNwDL5fOeMS5EJSvcmCyNhRmu6FVi+8g+1ZibreXliKxpUCiHUZP0gr5i1RGY\\nI/CmEmXFM6C409l7mEec9zGIjgjZLS0+BXufvNsyNJMZ+w5Gz6/KFH2ktyjxEukj\\n/X79TwKBgQCq5PgSK+yuUN7prBviD61GB+N6Sn+r1Y+aV+t7HNFfbBQL6/1jPu23\\nQpIophhJS6/thFBdIRyKvUa5Rl1WGSc5o9ra424zpezKRLRCm1xSY5wx1/8XjJpE\\n7mkTgRPnSib8Vjwfx4WWz5LFqZwBpinVDwlVUj6cRfRCE5ob1bue4A==\\n-----END RSA PRIVATE KEY-----\\n'
DOCUSIGN['INTEGRATION_KEY'] = '96779c0d-2a96-447a-b140-0157ffd19784'
DOCUSIGN['SECRET_KEY'] = 'ce9e26a1-a920-4cb0-8ee2-27a71a237f10'

QUICKBOOKS['CLIENT_ID'] = 'ABMlufrFmTTc6iqBLHw9Bzb2oInaeFdeZQs28gRSZ3mGOBL6Ha'
QUICKBOOKS['CLIENT_SECRET'] = 'uFhk2r3wsZKFDHl97cttMXSq2LiHkmz16jYUMmSc'
QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL'] = 'https://app.jus-law.com/dashboard'
QUICKBOOKS['ENVIRONMENT'] = 'production'

FCM_DJANGO_SETTINGS['FCM_SERVER_KEY'] = 'AAAAjlni0hE:APA91bHBBA4WIVw8jGE3_0n8yMCqtLR1chVWIOdQySWJgXqin6QLxLFUgdZl2lNZq0XzodFYbWnyMrkmnnnHEEgK4LBFOeuV5U2tIKK1ESdKLa2jPiiqwCZjKy5m29BtNhrq8POuOK9w'

TWILIO_ACCOUNT_SID = 'AC0ed12114c361442bcbe65be1567cff2a'
TWILIO_AUTH_TOKEN = 'fcb88a91f1dea762dbf2040748230913'
TWILIO_SERVICE = 'VA430b959bc7d9ce0a2dc80d57c885c866'