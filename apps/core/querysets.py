from typing import Iterable, Union

from django.db.models import QuerySet


class TaggedModelQuerySet(QuerySet):
    """QuerySet for model with 'taggit' fields."""

    def filler_by_tagged_field(
        self, tagged_field: str, tags: Iterable[Union[int, str]]
    ):
        """Filter query by tagged field(taggit)."""
        try:
            return self.filter(**{f'{tagged_field}__in': tags}).distinct()
        # If list of non ints was passe,then we should filter it by slug field
        except ValueError:
            return self.filter(
                **{f'{tagged_field}__slug__in': tags}
            ).distinct()
