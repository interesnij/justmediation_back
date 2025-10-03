from typing import Iterable, Union

from apps.core.querysets import TaggedModelQuerySet


class NewsQuerySet(TaggedModelQuerySet):
    """QuerySet for `News` model."""

    def filler_by_tags(self, tags: Iterable[Union[int, str]]):
        """Filter query by tags."""
        return self.filler_by_tagged_field(tagged_field='tags', tags=tags)

    def filler_by_categories(self, categories: Iterable[Union[int, str]]):
        """Filter query by categories."""
        return self.filler_by_tagged_field(
            tagged_field='categories', tags=categories
        )
