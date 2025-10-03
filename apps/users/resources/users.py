from django.db.models import Q

from import_export import resources
from import_export.fields import Field
from import_export.widgets import ManyToManyWidget

from .. import models, utils


class AppUserResource(resources.ModelResource):
    """Resource for `AppUser` model."""

    class Meta:
        model = models.AppUser
        fields = ('email',)


class SpecialitiesWidget(ManyToManyWidget):
    """Custom many to many widget specialities field.

    Made because when WorkPress exports specialities, it divides them by comma,
    and the problem is that some specialities contains comma and default
    ManyToManyWidget parses them incorrectly.

    """

    def clean(self, value, row=None, *args, **kwargs):
        """Search specialities by combination of icontains and Q expr."""
        if not value:
            return self.model.objects.none()
        titles = value.split(self.separator)
        titles = filter(None, [i.strip() for i in titles])
        q_conditions = Q()
        for title in titles:
            q_conditions |= Q(**{f'{self.field}__icontains': title})
        return self.model.objects.filter(q_conditions)


class InviteResource(resources.ModelResource):
    """Resource for `Invite` model.

    This resource was made to import data from register form in WordPress.

    """

    INVITE_MESSAGE = (
        'This invitation was auto generated, please follow link below'
    )

    specialities = Field(
        column_name='specialities',
        attribute='specialities',
        widget=SpecialitiesWidget(
            model=models.Speciality,
            field='title'
        )
    )

    class Meta:
        model = models.Invite
        fields = (
            'email',
            'first_name',
            'last_name',
            'specialities',
            'phone',
            'help_description',
            'user_type',
        )
        exclude = ('uuid',)
        import_id_fields = ('uuid',)

    def __init__(self, inviter: models.AppUser):
        """Add request and message to resource."""
        super().__init__()
        self.inviter = inviter

    def get_instance(self, instance_loader, row):
        """Fixes issue when we excluding `id` fields.

        This issue is appeared in django-import-export==2.0.2.
        https://github.com/django-import-export/django-import-export/pull/1056

        """
        for field_key in self.get_import_id_fields():
            if (
                field_key not in self.fields or
                self.fields[field_key].column_name not in row
            ):
                return
        return instance_loader.get_instance(row)

    def before_save_instance(
        self,
        instance: models.Invite,
        using_transactions,
        dry_run: bool
    ):
        """Set inviter in invitation and it's type to `imported`."""
        instance.inviter = self.inviter
        instance.type = models.Invite.TYPE_IMPORTED
        instance.message = self.INVITE_MESSAGE

    def after_save_instance(
        self,
        instance: models.Invite,
        using_transactions,
        dry_run: bool
    ):
        """Send invitation email after confirmed import."""
        if not dry_run:
            utils.send_invitation(instance)
