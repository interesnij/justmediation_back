from rest_framework.permissions import BasePermission


class IsCommentAuthor(BasePermission):
    """Check if user is comment author.

    This permission only works for views for `comment` model as it uses it's
    author field.

    """
    def has_object_permission(self, request, view, obj):
        """Check that user authored the post."""
        return request.user.id == obj.author.id


class IsPostAuthor(BasePermission):
    """Check if user created the post.

    This permission only works for views for `post` model as it uses it's
    first_comment field.
    """

    def has_object_permission(self, request, view, obj):
        from apps.forums.models import Comment
        if isinstance(obj, Comment):
            obj = obj.post
        return request.user.id == obj.author.id


class IsNotFirstComment(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.post.first_comment_id != obj.id
