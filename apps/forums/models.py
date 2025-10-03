from django.db import models
from django.utils.translation import gettext_lazy as _

from libs import utils

from apps.core.models import BaseModel
from ..users.models.users import AppUser
from ..forums import querysets

__all__ = (
    'Comment',
    'Topic',
    'Post',
    'FollowedPost',
    'UserStats',
)

def upload_topic_icons_to(instance, filename: str) -> str:
    """Upload topic icon to this folder.
    Returns:
        String. Generated path for image.
    """
    return 'forums/icons/{filename}'.format(
        filename=utils.get_random_filename(filename)
    )


def upload_category_icons_to(instance, filename: str) -> str:
    """Upload topic icon to this folder.
    Returns:
        String. Generated path for image.
    """
    return 'forums/icons/{filename}'.format(
        filename=utils.get_random_filename(filename)
    )


class ForumPracticeAreas(BaseModel):
    """
    Представлять практические области, связанные только с темами на форумах.
    Атрибуты:
        название (str): название области практики
        описание (str): описание области практики
    """

    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        unique=True,
    )
    description = models.TextField(
        verbose_name=_('Description'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Practice area')
        verbose_name_plural = _('Practice areas')

    def __str__(self):
        return self.title


class Topic(BaseModel):
    """ Представлять темы форума в базе данных.

    Темы форума высокого уровня, каждая тема связана с возможными
    Специальность адвоката (область практики), чтобы иметь возможность фильтровать
    Возможности для адвоката.

    Attributes:
        practice_area (users.Speciality): Foreign key to user
        specialities table.
        title (str): Brief description for topic.
        icon (str): Url for topic icon image.
        description (str): Topic description.
        comment_count (int): Number of comments within topic.
        post_count (int): Number of posts in Topic.
        last_comment_id (Post): Foreign key to last comment in topic.
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        featured (bool): Define if topic should be shown on main forum page.
        last_comment (Post): Last comment that was made in topic

    """
    followers = models.ManyToManyField(
        AppUser,
        verbose_name=_('Followers'),
        related_name='topics',
    )

    practice_area = models.ForeignKey(
        ForumPracticeAreas,
        verbose_name=_('Related practice area'),
        on_delete=models.PROTECT,
        related_name='forum_topics',
        null=True,
        blank=True,
    )
    title = models.CharField(
        _('Title'),
        max_length=255,
    )
    icon = models.CharField(
        _('Icon link'),
        max_length=255,
        null=True,
        blank=True,
    )
    description = models.TextField(
        _('Description'),
        null=True
    )
    comment_count = models.PositiveIntegerField(
        _('Number of comments in topic'),
        default=0,
    )
    last_comment = models.ForeignKey(
        'Comment',
        verbose_name=_('Last comment in topic'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    featured = models.BooleanField(
        _('Show on main page.'),
        default=True,
    )

    objects = querysets.TopicQuerySet.as_manager()

    class Meta:
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    def __str__(self):
        return f'{self.id}. {self.title}'

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def post_count(self):
        return self.posts.count()


class Post(BaseModel):
    """Post model

    Posts are a kind of threads (channels) with some amount of comments with
    from clients (appuser).

    Attributes:
        topic (Topic): Foreign key to Category model.
        title (str): title of Topic
        last_comment (int): Foreign key to last post in topic.
        first_comment (int): Foreign key to first post in topic.
        comment_count (int): Number of posts in topic.
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        followers (FollowedPost): Foreign key to FollowedPost model.
        author (AppUser): link to a AppUser who Created the post

    """
    topic = models.ForeignKey(
        'Topic',
        verbose_name=_('Topic'),
        on_delete=models.CASCADE,
        related_name='posts',
        null=True
    )
    title = models.CharField(
        _('Title'),
        max_length=255,
        null=True
    )
    last_comment = models.ForeignKey(
        'Comment',
        verbose_name=_('Last post on topic'),
        on_delete=models.SET_NULL,
        related_name='last_post_on_topic',
        null=True,
        blank=True,
    )
    first_comment = models.ForeignKey(
        'Comment',
        verbose_name=_('First comment on post'),
        on_delete=models.SET_NULL,
        related_name='first_post_on_post',
        null=True,
        blank=True,
    )
    comment_count = models.PositiveIntegerField(
        _('Number of comments on post'),
        default=0,
    )
    followers = models.ManyToManyField(
        AppUser,
        verbose_name=_('Followers'),
        through='FollowedPost',
        related_name='Post',
    )
    author = models.ForeignKey(
        AppUser,
        on_delete=models.PROTECT,
        verbose_name=_('Author'),
        related_name='posts',
        null=True
    )
    description = models.TextField(
        verbose_name=_('Description')
    )

    @property
    def followers_count(self):
        return self.followers.count()

    objects = querysets.PostQuerySet.as_manager()

    class Meta:
        verbose_name = _('Posts')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return f'{self.id}. {self.title}'


class Comment(BaseModel):
    """Comments model

    Comment is a client message/comment placed inside of some post (thread).

    Attributes:
        post (Post): link to a post in which comment is placed
        author (AppUser): link to a Client who is looking for Mediator
        text (text): text of the comment
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name=_('Post'),
        related_name='comments'
    )
    author = models.ForeignKey(
        AppUser,
        on_delete=models.PROTECT,
        verbose_name=_('Author'),
        related_name='comments'
    )
    text = models.TextField(
        _('Text of the comment'),
    )

    objects = querysets.CommentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return f'{self.id}. {self.text[:5]}... @ {self.author}'


class FollowedPost(BaseModel):
    """Many-to-many relation between users and topics.

    Attributes:
        follower (users.AppUser): Foreign key for user model.
        topic (Topic): Foreign key for topic model.
        unread_post_count (Post): number of unread posts for user in topic.
        last_read_post (Post): Foreign key for last post.

    """
    follower = models.ForeignKey(
        AppUser,
        verbose_name=_('Follower'),
        on_delete=models.CASCADE,
        related_name='followed_topics',
    )
    post = models.ForeignKey(
        'Post',
        verbose_name=_('Post'),
        on_delete=models.CASCADE,
    )
    unread_comments_count = models.PositiveIntegerField(
        _('Unread comments in post'),
        default=0,
    )
    last_read_comment = models.ForeignKey(
        'Comment',
        verbose_name=_('Last read comment'),
        related_name='last_read_comment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Follower of the Post')
        verbose_name_plural = _('Followers of Posts')
        unique_together = ('post', 'follower',)

    def __str__(self):
        return f'{self.id}. {self.post.title} followed by {self.follower}'


class UserStats(BaseModel):
    """Represent user statistic on forum.

    Pre-calculated statistics about forum using for users.

    Attributes:
        user (user.AppUser): Foreign key for user model.
        comment_count (Comment): Number of posts authored by user on forum.

    """
    user = models.OneToOneField(
        AppUser,
        verbose_name=_('User Statistic'),
        on_delete=models.CASCADE,
        related_name='forum_stats'
    )
    comment_count = models.PositiveIntegerField(
        _('Number of user comments on forum'),
        default=0,
    )

    class Meta:
        verbose_name = _('User Stats')
        verbose_name_plural = _('Users Stats')

    def __str__(self):
        return f'{self.user}'
