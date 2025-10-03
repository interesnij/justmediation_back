from django import forms

from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget

from apps.news import models


class NewsForm(forms.ModelForm):
    """For django-taggit-labels setup for admin panel."""
    categories = TagField(
        required=False,
        widget=LabelWidget(model=models.NewsCategory)
    )

    class Meta:
        model = models.News
        fields = (
            'title',
            'image',
            'description',
            'tags',
            'categories',
            'author'
        )
