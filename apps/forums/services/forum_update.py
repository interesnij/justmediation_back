from typing import Union

from apps.forums.models import Comment, Post, Topic, UserStats
from apps.users.models import AppUser


def set_last_comment(
    instance: Union[Topic, Post],
    last_comment: Comment = None,
):
    """Set last comment for `instance`.

    Set provided last comment for instance.
    If no `last_comment` were provide, this
    will fetch last comment from db.

    """
    if isinstance(instance, Topic):
        last_comment_filter = dict(post__topic=instance)

    elif isinstance(instance, Post):
        last_comment_filter = dict(post=instance)

    else:
        return

    if not last_comment:
        last_comment = Comment.objects \
            .filter(**last_comment_filter) \
            .order_by('-created') \
            .first()

    instance.last_comment = last_comment
    instance.save()


def set_first_comment(
    instance: Post,
    first_comment: Comment,
):
    """Set first comment for `instance`.
    """

    instance.first_comment = first_comment
    instance.save()


def set_comments_count(
    instance: Union[Topic, Post, AppUser],
    count: int = None,
):
    """Set posts count for `instance`.

    Increase posts count on count value. If no `count` were provide, this
    will count posts count in db query.

    """
    if isinstance(instance, AppUser):
        author = instance
        instance, _ = UserStats.objects.get_or_create(user=author)
        comment_count_filter = dict(author=author)

    elif isinstance(instance, Topic):
        comment_count_filter = dict(post__topic=instance)

    elif isinstance(instance, Post):
        comment_count_filter = dict(post=instance)

    else:
        return

    if count:
        instance.comment_count = instance.comment_count + count
    else:
        instance.comment_count = Comment.objects \
            .filter(**comment_count_filter) \
            .count()

    instance.save()


def update_all():
    """Update all categories, topics and user stats objects."""

    for category in Topic.objects.all():
        set_last_comment(category)
        set_comments_count(category)

    for post in Post.objects.distinct('author'):
        set_comments_count(post.author)
