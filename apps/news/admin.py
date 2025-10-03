from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from imagekit.admin import AdminThumbnail
from taggit.admin import TagAdmin

from ..core.admin import BaseAdmin
from . import models
from .forms import NewsForm


@admin.register(models.News)
class NewsAdmin(BaseAdmin):
    """Django Admin for `News`."""
    form = NewsForm
    search_fields = ('title',)
    list_display = (
        'id',
        'title',
        'created',
        'modified',
    )
    list_display_links = (
        'id',
        'title',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'image',
                'image_thumbnail',
                'description',
                'tags',
                'categories',
                'author'
            )
        }),
    )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        user = obj.author if obj and obj.author else request.user
        form.base_fields['author'].queryset = get_user_model().objects.filter(
            id=user.id)
        form.base_fields['author'].initial = user
        return form


@admin.register(models.NewsTag)
class NewsTagAdmin(TagAdmin):
    """Django Admin for `NewsTag`."""
    inlines = []


@admin.register(models.NewsCategory)
class NewsCategoryAdmin(TagAdmin):
    """Django Admin for `NewsCategory`."""
    inlines = []
