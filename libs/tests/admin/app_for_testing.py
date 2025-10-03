from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from libs.admin.mixins import AllFieldsReadOnly


class Post(models.Model):
    """Test model for ``FkAdminLinkTestCase``"""
    title = models.CharField(max_length=255)
    text = models.TextField()

    def __str__(self):
        return self.title


class PostForm(ModelForm):
    """Test form to check extending field excluding in
     ``AllFieldsReadOnlyTestCase``"""

    class Meta:
        model = Post
        exclude = ['title']


class PostAdmin(AllFieldsReadOnly, admin.ModelAdmin):
    pass


class PostAdminWithFieldsAttr(AllFieldsReadOnly, admin.ModelAdmin):
    fields = ['test_field']


class PostAdminWithExcludeField(AllFieldsReadOnly, admin.ModelAdmin):
    exclude = ['title']


class PostAdminWithExcludeFieldInForm(AllFieldsReadOnly, admin.ModelAdmin):
    form = PostForm
