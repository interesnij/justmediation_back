from datetime import datetime

from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Count, F, Q, QuerySet

from apps.users.models import AppUser

__all__ = (
    'PostQuerySet',
)


class PostQuerySet(QuerySet):
    """QuerySet class for `Post` model."""

    def opportunities(self, user: AppUser):
        """Get opportunities for mediator.

        Opportunity is now determined by this logic:
        Post is opportunity when client's state is one of mediator's practice
        jurisdiction, and a post's category matches with mediator's specialty
        or post's first comment or title contains keywords that are saved in
        mediator's profile.

        In other words:
            If (
                client_state in mediator_practice_jurisdiction and
                (
                    client_specialty in mediator_specialty or (
                        mediator_keywords in post_title or in
                        post_first_comment
                    )
                )
            ):
            post is opportunity for mediator

        """
        qs_filtered_states = self.by_mediator_practice_jurisdictions(user=user)

        keywords = user.mediator.keywords
        if not keywords:
            return qs_filtered_states.by_user_specialties(user)

        return qs_filtered_states.by_mediator_specialties_or_keywords(user)

    def by_user_specialties(self, user: AppUser):
        """Filter posts by user's specialities."""
        specialities = user.specialities.all()
        return self.filter(
            topic__practice_area__in=specialities
        )

    def by_mediator_specialties_or_keywords(self, user: AppUser):
        """Filter topics by mediator's specialities or keywords."""
        # Prevent import error
        from .services import convert_keywords_to_querytext

        specialities = user.specialities.all()
        keywords = user.mediator.keywords
        search_querytext = convert_keywords_to_querytext(keywords)
        search_query = SearchQuery(search_querytext, search_type='raw')
        qs_with_search_vector = self.annotate(
            search=SearchVector('title', 'first_comment__text')
        )
        return qs_with_search_vector.filter(
            Q(topic__practice_area__in=specialities) | Q(search=search_query)
        )

    def by_mediator_practice_jurisdictions(self, user: AppUser):
        """Filter posts by mediator's practice jurisdictions."""
        mediator = user.mediator
        practice_jurisdictions = mediator.practice_jurisdictions.values_list(
            'state',
            flat=True
        )

        return self.filter(
            first_comment__author__client__state__id__in=practice_jurisdictions
        )

    def opportunities_for_period(
        self,
        user: AppUser,
        period_start: datetime,
        period_end: datetime
    ):
        """Get opportunities for period of time."""
        return self.opportunities(user=user).filter(
            created__gte=period_start, created__lte=period_end
        )


class TopicQuerySet(QuerySet):
    """QuerySet class for `Topic` model."""

    def by_user_specialties(self, user: AppUser):
        """Filter posts by user's specialities."""
        specialities = user.specialities.all()
        return self.filter(
            practice_area__in=specialities
        )

    def opportunities(self, user: AppUser):
        """Get opportunities for mediator."""
        qs_filtered_states = self.by_mediator_practice_jurisdictions(user=user)

        keywords = user.mediator.keywords
        if not keywords:
            return qs_filtered_states.by_user_specialties(user)

        return qs_filtered_states.by_mediator_specialties_or_keywords(user)

    def opportunities_for_period(
        self,
        user: AppUser,
        period_start: datetime,
        period_end: datetime
    ):
        """Get opportunities for period of time."""
        return self.opportunities(user=user).filter(
            created__gte=period_start, created__lte=period_end
        )

    def by_mediator_practice_jurisdictions(self, user: AppUser):
        """Filter posts by mediator's practice jurisdictions."""
        mediator = user.mediator
        practice_jurisdictions = mediator.practice_jurisdictions.values_list(
            'state',
            flat=True
        )

        return self.filter(
            last_comment__author__client__state__id__in=practice_jurisdictions
        )


class CommentQuerySet(QuerySet):
    """QuerySet class for `Post` model."""

    def with_position(self):
        """Add post position to queryset."""
        return self.annotate(
            position=Count(
                'post__comments', filter=Q(
                    post=F('post'),
                    post__comments__created__lt=F('created')
                )
            )
        )
