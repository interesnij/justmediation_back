from typing import Any

from django.conf import settings
from django.core.management import BaseCommand

from apps.finance.constants import PlanTypes
from apps.finance.models import PlanProxy, ProductProxy

STANDARD_DESC = """Get access to all features justmediationhub has to offer! Use the
justmediationhub forum to answer potential client questions, convert potentials to be
your clients via in-app chats, create matters for your new clients, bill your
time, and invoice and more."""


PREMIUM_DESC = """Get access to standard features and more! Appear first to a
potential client when they search for mediators, appear as a featured
mediator on the justmediationhub homepage. The premium subscription gives you the most
visibility on justmediationhub and much more."""


class Command(BaseCommand):
    """ Пользовательский интерфейс для создания продуктов и планов stripe
        Создайте продукт и планы по умолчанию для целей тестирования.
    """
    help = """Script for fast creation product and plans"""

    def handle(self, *args: Any, **options: Any) -> None:
        assert settings.ENVIRONMENT != 'local'
        product_annual_args = {
            'name': 'Annual Subscription',
            'type': 'service',
            'active': True
        }
        product_annual = ProductProxy.create(**product_annual_args)

        product_monthly_args = {
            'name': 'Monthly Subscription',
            'type': 'service',
            'active': True
        }
        product_monthly = ProductProxy.create(**product_monthly_args)

        plan_args = {
            'active': True,
            'billing_scheme': 'per_unit',
            'currency': 'usd',
            'interval_count': 1,
            'usage_type': 'licensed',
        }
        plan_args_annual = plan_args.copy()
        plan_args_annual.update(
            {
                'product': product_annual.id,
                'interval': 'year',
                'metadata': {'type': PlanTypes.PREMIUM}
            },
        )
        plan_annual = PlanProxy.create(
            **plan_args_annual,
            nickname=PlanTypes.PREMIUM,
            amount=576.00
        )
        plan_args_monthly = plan_args.copy()
        plan_args_monthly.update(
            {
                'product': product_monthly.id,
                'interval': 'month',
                'metadata': {'type': PlanTypes.STANDARD}
            },
        )
        plan_monthly = PlanProxy.create(
            **plan_args_monthly,
            nickname=PlanTypes.STANDARD,
            amount=58.00
        )

        self.stdout.write(
            f'''Created: \n
            Product premium: {product_monthly}\n
            Plan premium by year: {plan_monthly}\n
            Product standard: {product_annual}\n
            Plan standard by year: {plan_annual}\n'''
        )
