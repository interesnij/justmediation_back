from django.db.models import Count, QuerySet

from apps.users.models import AppUser


class ChatQuerySet(QuerySet):

    def available_for_user(self, user: AppUser):
        return self.filter(participants=user).distinct()

    def already_existing_chat(self, participants):
        """Write logic to filter by exact participants"""
        from apps.social.models import Chats
        chats = Chats.objects.annotate(
            count=Count('participants')
        ).filter(count=len(participants))
        for participant in participants:
            chats = chats.filter(participants=participant)
        return chats.first()
