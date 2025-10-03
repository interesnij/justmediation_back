# all these params should be overridden for each environment configs
QUICKBOOKS_ENABLED = True
QUICKBOOKS = {
    'CLIENT_ID': None,
    'CLIENT_SECRET': None,
    'ENVIRONMENT': 'sandbox',
    'AUTH_REDIRECT_URL': 'api/v1/accounting/auth/callback/',
    # required for correct auth workflow
    'BASE_AUTH_ERROR_REDIRECT_URL': None,
}
