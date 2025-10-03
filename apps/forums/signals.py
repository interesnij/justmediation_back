from django.db.models import signals
from django.dispatch import Signal, receiver

from apps.forums.models import Comment, Post
from apps.forums.services import forum_update
from apps.forums.services.forum_update import set_first_comment

new_opportunities_for_mediator = Signal(providing_args=('instance',))
new_opportunities_for_mediator.__doc__ = (
    'Signal which indicates that there are new opportunities for mediator'
)
new_comment_on_post = Signal(providing_args=('instance',))
new_comment_on_post.__doc__ = (
    'Signal which indicates that there are new comments on post'
    "and we should notify post's followers"
)
new_post_on_topic = Signal(providing_args=('instance',))
new_post_on_topic.__doc__ = (
    'Signal which indicates that there are new posts on topic'
    "and we should notify topic's followers"
)
new_comment_on_post_by_mediator = Signal(providing_args=('instance',))
new_comment_on_post_by_mediator.__doc__ = (
    'Signal which indicates that there are new comments on post'
    "made by mediator and we should notify mediator's followers"
)


@receiver(signals.post_save, sender=Post)
def new_post_created(instance: Post, created: bool, **kwargs):
    """Send signal about new post creation.
    """
    if not created:
        return

    new_post_on_topic.send(sender=Post, instance=instance)


@receiver(signals.post_save, sender=Comment)
def new_post(instance: Comment, created: bool, **kwargs):
    """Send signal about new comment.

    We send two different signals:
        new_comment_on_post is always sent
        new_comment_on_post_by_mediator is sent if author of post is mediator

    """
    if not created:
        return

    if not instance.post.first_comment:
        set_first_comment(instance=instance.post, first_comment=instance)

    new_comment_on_post.send(sender=Comment, instance=instance)
    if instance.author.is_mediator:
        new_comment_on_post_by_mediator.send(sender=Comment, instance=instance)


@receiver(signals.post_save, sender=Comment)
def post_creation(instance: Comment, created: bool, **kwargs):
    """Perform recalculation for statistic data in related models."""
    if not created:
        return

    # Update related topic
    forum_update.set_last_comment(instance.post, instance)
    forum_update.set_comments_count(instance.post, 1)

    # Update related category
    forum_update.set_last_comment(instance.post.topic, instance)
    forum_update.set_comments_count(instance.post.topic, 1)

    # Update post's author user stats
    forum_update.set_comments_count(instance.author, 1)


@receiver(signals.post_delete, sender=Comment)
def post_deletion(instance: Comment, **kwargs):
    """Perform recalculation for statistic data in related models.

    Update topic and category statistic in case of post deletion.

    """
    # Update related topic
    forum_update.set_comments_count(instance.post)
    forum_update.set_last_comment(instance.post)
    # Update related category
    forum_update.set_comments_count(instance.post.topic)
    forum_update.set_last_comment(instance.post.topic)
    # Update user statistic
    forum_update.set_comments_count(instance.author)
