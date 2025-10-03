from ...forums import models
from ...users.models import Mediator

__all__ = (
    'get_mediator_statistics',
    'get_stats_for_dashboard',
)


def get_mediator_statistics(mediator: Mediator) -> dict:
    """Get mediator statistics for forums app."""
    opportunities_count = models.Topic.objects.opportunities(
        mediator.user
    ).count()

    return {
        'opportunities_count': opportunities_count,
    }


def get_stats_for_dashboard():
    """Collect forums stats for admin dashboard."""
    statistics = [
        {
            'stats_msg': 'Topics count',
            'stats': models.Topic.objects.all().count(),
        },
        {
            'stats_msg': 'Posts count',
            'stats': models.Post.objects.all().count(),
        },
    ]

    return statistics
