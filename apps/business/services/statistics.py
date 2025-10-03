from datetime import datetime

from ...business import models, services
from ...users.models import Mediator


def get_mediator_statistics(mediator: Mediator) -> dict:
    """Get mediator statistics for business app."""
    active_leads_count = mediator.leads.filter(
        status=models.Lead.STATUS_ACTIVE
    ).count()
    active_matters_count = mediator.matters.filter(
        status=models.Matter.STATUS_OPEN
    ).count()

    return {
        'active_leads_count': active_leads_count,
        'active_matters_count': active_matters_count,
    }


def get_mediator_period_statistic(
    mediator: Mediator,
    start: datetime,
    end: datetime,
    time_frame: str = 'month'
) -> dict:
    """Get mediator statistics for period of time divided by time frame.

    Get mediator statistics for period of time divided by time frame from
    business app.


    """
    time_billed = services.get_time_billing_for_time_period(
        user=mediator.user, start=start, end=end, time_frame=time_frame
    )
    return {
        'time_billed': time_billed,
    }


def get_stats_for_dashboard() -> list:
    """Collect business stats for admin dashboard."""
    matters_stats = models.Matter.objects.aggregate_count_stats()
    leads_stats = models.Lead.objects.aggregate_count_stats()
    statistics = [
        {
            'stats_msg': 'Open matters',
            'stats': matters_stats['open_count'],
        },
        {
            'stats_msg': 'Referred matters',
            'stats': matters_stats['referred_count'],
        },
        {
            'stats_msg': 'Closed matters',
            'stats': matters_stats['closed_count'],
        },
        {
            'stats_msg': 'Total matters count',
            'stats': matters_stats['total_count'],
        },
        {
            'stats_msg': 'Active leads',
            'stats': leads_stats['active_count'],
        },
        {
            'stats_msg': 'Converted leads',
            'stats': leads_stats['converted_count'],
        },
        {
            'stats_msg': 'Total leads count',
            'stats': leads_stats['total_count'],
        },

    ]

    return statistics
