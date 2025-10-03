from django.db import models
from django.utils.translation import gettext_lazy as _

from taggit.models import GenericTaggedItemBase, TagBase


class NewsTag(TagBase):
    """Tags for `News` model."""

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class NewsTagLink(GenericTaggedItemBase):
    """Model for creating links between news tag and other models.

    Used to get all features and support from taggit package.

    """
    tag = models.ForeignKey(
        NewsTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )


class NewsCategory(TagBase):
    """Categories for `News` model."""

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class NewsCategoriesLink(GenericTaggedItemBase):
    """Model for creating links between news category and other models.

    Used to get all features and support from taggit package.

    """
    tag = models.ForeignKey(
        NewsCategory,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )
