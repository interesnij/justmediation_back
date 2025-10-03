# Usage for initial subscriptions
PROMO_PERIOD_MONTH = 6


class PlanTypes:
    """ Перечисление типов планов подписки для Proxymodel плана ."""
    PREMIUM = 'premium'
    STANDARD = 'standard'


class Capabilities:
    """ Перечисление запрошенных учетной записью приложения привилегий для Stripe connect API.
    https://stripe.com/docs/connect/account-capabilities
    """
    CAPABILITY_CARD_PAYMENTS = 'card_payments'
    CAPABILITY_TRANSFERS = 'transfers'
    CAPABILITY_TAX_REPORTING_US_1099_MISC = 'tax_reporting_us_1099_misc'
    CAPABILITY_TAX_REPORTING_US_1099_K = 'tax_reporting_us_1099_k'

    default = [
        CAPABILITY_CARD_PAYMENTS,
        CAPABILITY_TRANSFERS,
        CAPABILITY_TAX_REPORTING_US_1099_MISC,
        CAPABILITY_TAX_REPORTING_US_1099_K
    ]
