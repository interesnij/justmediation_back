from datetime import datetime

from dateutil.relativedelta import relativedelta

from ..constants import PROMO_PERIOD_MONTH


def calculate_promo_subscription_period(
    start_date: datetime,
    months: int = PROMO_PERIOD_MONTH,
) -> datetime:
    """Calculate promo datetime value for not created subscription"""
    promo_date = start_date + relativedelta(months=months)
    return promo_date


def get_promo_period_timestamp(period_start: datetime) -> int:
    """Calculate promo datetime as timestamp"""
    promo_date = calculate_promo_subscription_period(period_start)
    return round(promo_date.timestamp())
