from apps.business.models import MatterComment, MatterPost


# TODO: Refactor in single class with forum app
def set_matter_post_comment_count(post: MatterPost, increase_by: int = None):
    """Increase comment_count value for `MatterPost` instance.

    Arguments:
        post: post instance to be modified.
        increase_by: number to increase post's comment count.

    """
    if increase_by:
        post.comment_count = post.comment_count + increase_by
    else:
        post.comment_count = post.comments.count()
    post.save()


def set_matter_post_last_comment(
    post: MatterPost, last_comment: MatterComment = None
):
    """Set last_post value for `MatterTopic` instance."""
    if last_comment:
        post.last_comment = last_comment
    else:
        post.last_comment = post.comments.order_by('-created').first()
    post.save()
