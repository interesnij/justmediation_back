from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..core import admin as core_admin
from . import models


@admin.register(models.ForumPracticeAreas)
class PracticeAreaAdmin(core_admin.BaseAdmin):
    """Admin UI for Topic model."""
    list_display = (
        'id',
        'title',
    )
    fields = (
        'id',
        'title',
        'description',
    )
    search_fields = ('title',)
    ordering = ('title',)


@admin.register(models.Topic)
class TopicAdmin(core_admin.BaseAdmin):
    """Admin UI for Topic model."""
    autocomplete_fields = (
        'practice_area',
    )
    list_display = (
        'id',
        'title',
        'practice_area',
    )
    list_display_links = (
        'id',
        'title'
    )
    list_select_related = (
        'practice_area',
    )
    fields = (
        'title',
        'practice_area',
        'icon',
        'icon_display',
        'description',
        'post_count',
        'comment_count',
        'last_comment',
    )
    search_fields = ('title',)
    ordering = ('title',)
    readonly_fields = (
        'icon_display',
        'post_count',
        'comment_count',
        'last_comment',
    )
    create_only_fields = (
        'practice_area',
    )
    autocomplete_list_filter = (
        'practice_area',
    )

    def last_comment(self, obj):
        return self._admin_url(obj.last_comment) if obj.last_comment else '-'

    def icon_display(self, obj):
        """Return html tag with icon if has one(if not return '-')."""
        if obj.icon:
            return format_html(mark_safe(f'<img src="{obj.icon.url}">'))
        return '-'

    icon_display.short_description = 'Icon'


@admin.register(models.Post)
class PostAdmin(core_admin.BaseAdmin):
    """Django Admin for Post model."""
    autocomplete_fields = (
        'topic',
    )
    list_display = (
        'id',
        'title',
        'topic',
        'comment_count',
        'last_comment',
        'first_comment',
    )
    list_display_links = (
        'id',
        'title',
    )
    fields = (
        'title',
        'topic',
        'comment_count',
        'last_comment',
        'first_comment',
    )
    search_fields = ('title',)
    readonly_fields = (
        'comment_count',
        'last_comment',
        'first_comment',
    )
    create_only_fields = (
        'topic',
    )
    ordering = (
        'created',
        'topic',
    )
    related_models = (
        models.Comment,
    )
    list_select_related = (
        'topic',
        'last_comment__author',
        'first_comment__author',
    )
    autocomplete_list_filter = (
        'topic',
    )

    def last_comment(self, obj):
        return self._admin_url(obj.last_comment) if obj.last_post else '-'

    def first_comment(self, obj):
        return self._admin_url(obj.first_comment) if obj.first_post else '-'


@admin.register(models.FollowedPost)
#class FollowedPostAdmin(core_admin.ReadOnlyAdmin):
class FollowedPostAdmin(admin.ModelAdmin):
    """Admin UI for FollowedTopic admin."""
    autocomplete_fields = (
        'follower',
        'post'
    )
    list_display = (
        'post',
        'follower',
    )
    search_fields = (
        'post__title',
    )
    fields = (
        'follower',
        'post',
        'unread_comments_count',
        'last_read_comment',
    )
    readonly_fields = (
        'unread_comments_count',
        'last_read_comment',
    )
    autocomplete_list_filter = (
        'post',
        'follower',
    )


@admin.register(models.Comment)
class CommentAdmin(core_admin.BaseAdmin):
    """Django Admin for Post model."""
    list_display = (
        'id',
        'post',
        'author',
        'text',
    )
    fields = (
        'post',
        'author',
        'text',
    )
    list_display_links = (
        'id',
        'post',
    )
    search_fields = (
        'post__title',
    )
    ordering = (
        'created',
        'post',
    )
    create_only_fields = (
        'post',
        'author',
    )
    autocomplete_fields = (
        'post',
        'author',
    )
    autocomplete_list_filter = (
        'post',
        'author',
    )


@admin.register(models.UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    """Admin UI for UserStats model."""
    list_display = (
        'user',
        'comment_count',
    )
    fields = (
        'user',
        'comment_count',
    )
    readonly_fields = (
        'user',
        'comment_count',
    )
    search_fields = (
        'user__first_name',
        'user__last_name',
    )
    autocomplete_list_filter = (
        'user',
    )
