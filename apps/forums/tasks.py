from django.utils.datetime_safe import datetime

import arrow

from config.celery import app

from ..users import models as user_models
from ..users.services import create_stat
from . import models


@app.task()
def calculate_opportunities_for_today():
    """Celery task to generate Opportunities stats for mediators.

    At the beginning of each day, we calculate the amount of opportunities for
    mediator what was posted yesterday. We calculate this stats only for
    verified mediators.

    """
    today = arrow.get(datetime.now())
    yesterday = today.shift(days=-1)
    verified_mediators = user_models.Mediator.objects.verified()

    for mediator in verified_mediators:
        opportunities_count = models.Topic.objects.opportunities_for_period(
            user=mediator.user,
            period_start=yesterday.datetime,
            period_end=today.datetime,
        ).count()

        create_stat(
            user=mediator.user,
            tag=user_models.UserStatistic.TAG_OPPORTUNITIES,
            count=opportunities_count
        )
