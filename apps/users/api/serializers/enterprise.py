from rest_framework import serializers
from ....core.api.serializers import BaseSerializer
from ....users import models
from ...models import AppUser
from ...models.enterprise_link import EnterpriseMembers
from .auth import AppUserRelatedRegisterSerializerMixin
from .enterprise_link import MemberSerializer
from .extra import FirmLocationSerializer, FirmSizeSerializer


class EnterpriseSerializer(BaseSerializer):
    """Serializer for Enterprise model."""
    firm_locations = FirmLocationSerializer(
        many=True, required=False
    )
    team_members = serializers.SerializerMethodField()
    team_members_registered_data = serializers.SerializerMethodField()
    firm_size_data = FirmSizeSerializer(
        source='firm_size', read_only=True
    )

    class Meta:
        model = models.Enterprise
        fields = (
            'id',
            'team_logo',
            'is_verified',
            'verification_status',
            'followers',
            'featured',
            'role',
            'firm_name',
            'firm_size',
            'firm_size_data',
            'firm_locations',
            'team_members',
            'team_members_registered',
            'team_members_registered_data',
        )
        read_only_fields = (
            'user',
            'verification_status',
            'followers',
            'featured',
        )
        relations = (
            'user',
            'firm_locations',
            'firm_size'
        )

    def to_representation(self, instance):
        if instance.team_logo == '[]':
            instance.team_logo = None
        data = super().to_representation(instance=instance)
        return data

    def get_team_members(self, obj):
        members = []
        for m in obj.team_members_invited.all():
            data = MemberSerializer(m).data
            invite = EnterpriseMembers.objects.get(enterprise=obj, invitee=m)
            data.update({
                'state': invite.state,
                'type': invite.type
            })
            members.append(data)
        return members

    def get_team_members_registered_data(self, obj):
        members = []
        from apps.users.api.serializers import (
            MediatorShortSerializer,
        )
        for m in obj.team_members_registered.all():
            if m.is_mediator:
                data = MediatorShortSerializer(m.mediator).data
            else:
                continue
            data.update({'state': EnterpriseMembers.objects.get(
                enterprise=obj, user=m).state})
            members.append(data)
        return members


class EnterpriseRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, EnterpriseSerializer
):
    """RegisterSerializer for Enterprise"""

    class Meta(EnterpriseSerializer.Meta):
        fields = EnterpriseSerializer.Meta.fields + (
            'password1',
            'password2'
        )
        relations = EnterpriseSerializer.Meta.relations + (
            'email',
            'avatar',
            'first_name',
            'middle_name',
            'last_name'
        )
        extra_kwargs = {
            'firm_name': {
                'required': False
            }
        }

    def validate(self, data):
        """ Проверьте регистрационные данные """
        data = super().validate(data)
        return super(EnterpriseSerializer, self).validate(data)

    def create_related(self, user):
        """ Сохранить корпоративную запись """
        enterprise_data = self.validated_data.copy()
        enterprise_data['user'] = user
        _admin = models.Enterprise.objects.create(**enterprise_data)
        _enterprise = models.Enterprise.objects.get(user=_admin)
        firm_locations = enterprise_data.pop(
            'firm_locations', []
        ) 

        # Создать профиль местоположения фирмы
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            _admin.firm_locations.add(location)
            _enterprise.firm_locations.add(location)

    def create_entry(self, user):
        """ Используется для создания корпоративной записи без создания пользователя """
        enterprise_data = self.validated_data.copy()
        for key in self.validated_data:
            if key not in ['role', 'firm_size']:
                del enterprise_data[key]
        enterprise_data['user'] = user
        models.Enterprise.objects.create(**enterprise_data)


class EnterpriseOnboardingSerializer(EnterpriseSerializer):
    """ Встроенный сериализатор для предприятия """
    team_members = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False
    )
    team_members_registered = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta(EnterpriseSerializer.Meta):
        read_only_fields = EnterpriseSerializer.Meta.read_only_fields + \
                           ('role',)

    def validate(self, data):
        """ Проверьте регистрационные данные """
        team_members_registered = data.pop('team_members_registered', None)
        team_members = data.pop('team_members', None)
        data = super().validate(data)

        if team_members is not None:
            for m in team_members:
                if AppUser.objects.filter(email=m['email']).exists():
                    raise serializers.ValidationError(
                        "User with email '{}' already exist".format(m['email'])
                    )
            data.update({'team_members': team_members})
        if team_members_registered is not None:
            for user_id in team_members_registered:
                if not AppUser.objects.filter(pk=user_id).exists():
                    raise serializers.ValidationError(
                        "User with id={} does not exist".format(user_id)
                    )
                user = AppUser.objects.get(pk=user_id)
                if user.is_enterprise_admin:
                    raise serializers.ValidationError(
                        "Enterprise admin user(id={}) can't be invited".format(
                            user_id))
                if not user.is_mediator:
                    raise serializers.ValidationError(
                        "Client user(id={}) can't be member of team".format(
                            user_id))
            data.update({'team_members_registered': team_members_registered})
        return data

    def update(self, enterprise_id, validated_data):
        enterprise = models.Enterprise.objects.get(pk=enterprise_id)

        firm_locations = validated_data.pop(
            'firm_locations', []
        )

        # Create firm locations
        for obj in enterprise.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            enterprise.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            enterprise.firm_locations.add(location)

        # Create team members
        if 'team_members' in validated_data:
            team_members = validated_data.pop(
                'team_members', []
            )
            for obj in team_members:
                member, created = models.Member.objects.get_or_create(
                    email=obj['email']
                )
                if not models.EnterpriseMembers.objects.filter(
                    enterprise=enterprise,
                    invitee=member
                ).exists():
                    member._send_invitation(enterprise, obj['type'])
                    enterprise.team_members_invited.add(
                        member,
                        through_defaults={'type': obj['type']}
                    )
        if 'team_members_registered' in validated_data:
            team_members = validated_data.pop(
                'team_members_registered', []
            )

            members_existing = EnterpriseMembers.objects.filter(
                enterprise=enterprise,
                user__isnull=False
            ).values_list('user__id', flat=True)
            members_to_add = [
                m for m in team_members if m not in members_existing
            ]

            for m in members_to_add:
                user = models.AppUser.objects.get(pk=m)
                enterprise.team_members_registered.add(
                    user,
                    through_defaults={
                        'type': EnterpriseMembers.USER_TYPE_MEDIATOR
                    }
                )
        super().update(enterprise, validated_data)
        return models.Enterprise.objects.get(pk=enterprise_id)


class EnterpriseMediatorOnboardingSerializer(EnterpriseOnboardingSerializer):
    """ Встроенный сериализатор для предприятия/адвоката """

    class Meta(EnterpriseOnboardingSerializer.Meta):
        read_only_fields = EnterpriseOnboardingSerializer.Meta.read_only_fields

    def validate(self, data):
        return super().validate(data)

    def update(self, enterprise_id, validated_data):
        enterprise = super().update(enterprise_id, validated_data)
        user = enterprise.user
        """ Обновите модель адвоката, связанную с администратором предприятия """
        from apps.users.api.serializers import MediatorOnboardingSerializer
        serializer = MediatorOnboardingSerializer(
            data=self.context['request'].data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mediator = serializer.update(user.pk, data)
        user = mediator.user
        user.onboarding = True
        user.save()

        return enterprise


class EnterpriseOtherOnboardingSerializer(EnterpriseOnboardingSerializer):
    """ Встроенный сериализатор для предприятия-помощник юриста-другое """

    class Meta(EnterpriseOnboardingSerializer.Meta):
        read_only_fields = EnterpriseOnboardingSerializer.Meta.read_only_fields

    def validate(self, data):
        return super().validate(data)

    def update(self, enterprise_id, validated_data):
        enterprise = super().update(enterprise_id, validated_data)
        user = enterprise.user
        """ Обновить модель помощника юриста, связанную с администратором предприятия """
        from apps.users.api.serializers import (
            EnterpriseOnboardingSerializer,
        )
        serializer = EnterpriseOnboardingSerializer(
            data=self.context['request'].data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        other = serializer.update(user.pk, data)
        user = other.user
        user.onboarding = True
        user.save()

        return enterprise


class EnterpriseAndAdminUserSerializer(
    EnterpriseSerializer
):
    """ Сериализатор для предприятий и администраторов. """
    admin_user_data = serializers.SerializerMethodField()
    team_members_stats = serializers.SerializerMethodField()

    class Meta(EnterpriseSerializer.Meta):
        fields = EnterpriseSerializer.Meta.fields + (
            'admin_user_data',
            'team_members_stats',
        )

    def get_admin_user_data(self, obj):
        if obj.user.is_mediator:
            from apps.users.api.serializers import MediatorSerializer
            return MediatorSerializer(obj.user.mediator).data
        return None

    def get_team_members_stats(self, obj):
        mediator_count = len([
            m for m in obj.team_members_registered.all() if m.is_mediator
        ])
        pending_invites_count = obj.team_members_invited.count()
        seats_used = mediator_count + \
            pending_invites_count
        return {
            'mediator_count': mediator_count,
            'other_count': 0,
            'pending_invites_count': pending_invites_count,
            'seats_used': seats_used,
            'seats_available':
                int(obj.firm_size.title.split('-')[-1].split('+')[0])
        }


class UpdateEnterpriseSerializer(EnterpriseAndAdminUserSerializer):
    team_members = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        write_only=True
    )
    team_members_data = serializers.SerializerMethodField()
    team_members_registered = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta(EnterpriseAndAdminUserSerializer.Meta):
        fields = EnterpriseAndAdminUserSerializer.Meta.fields + (
            'team_members_data',
        )
        read_only_fields = EnterpriseAndAdminUserSerializer. \
            Meta.read_only_fields + (
                'role',
                'admin_user_data'
            )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['team_members'] = data.pop('team_members_data', None)
        return data

    def get_team_members_data(self, obj):
        members = []
        for m in obj.team_members_invited.all():
            data = MemberSerializer(m).data
            invite = EnterpriseMembers.objects.get(enterprise=obj, invitee=m)
            data.update({
                'state': invite.state,
                'type': invite.type
            })
            members.append(data)
        return members

    def validate(self, data):
        """ Проверьте регистрационные данные """
        team_members_registered = data.pop('team_members_registered', None)
        data = super().validate(data)
        if len(data.get('team_members', [])) > 20:
            raise serializers.ValidationError(
                "Exceed maximum number of team members"
            )
        for m in data.get('team_members', []):
            if AppUser.objects.filter(email=m['email']).exists():
                raise serializers.ValidationError(
                    "User with email '{}' already exist".format(m['email'])
                )
        if team_members_registered is not None:
            for user_id in team_members_registered:
                if not AppUser.objects.filter(pk=user_id).exists():
                    raise serializers.ValidationError(
                        "User with id={} does not exist".format(user_id)
                    )
                user = AppUser.objects.get(pk=user_id)
                if user.is_enterprise_admin:
                    raise serializers.ValidationError(
                        "Enterprise admin user(id={}) can't be invited".format(
                            user_id))
                if not user.is_mediator:
                    raise serializers.ValidationError(
                        "Client user(id={}) can't be member of team".format(
                            user_id))
            data.update({'team_members_registered': team_members_registered})
        return data

    def update(self, enterprise, validated_data):
        user = enterprise.user
        """ Обновить модель адвоката/помощника юриста, связанную с администратором предприятия """
        if user.is_mediator:
            from apps.users.api.serializers import UpdateMediatorSerializer
            serializer = UpdateMediatorSerializer(
                data=self.context['request'].data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            serializer.update(user.mediator, data)

        firm_locations = validated_data.pop(
            'firm_locations', []
        )

        # Update firm location
        for obj in enterprise.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            enterprise.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            enterprise.firm_locations.add(location)

        # Update team member
        if 'team_members' in validated_data:
            team_members = validated_data.pop(
                'team_members', []
            )
            EnterpriseMembers.objects.filter(
                enterprise=enterprise,
                invitee__isnull=False
            ).delete()
            for obj in team_members:
                member, created = models.Member.objects.get_or_create(
                    email=obj['email']
                )
                if not models.EnterpriseMembers.objects.filter(
                    enterprise=enterprise,
                    invitee=member
                ).exists():
                    member._send_invitation(enterprise, obj['type'])
                    enterprise.team_members_invited.add(
                        member,
                        through_defaults={'type': obj['type']}
                    )
        if 'team_members_registered' in validated_data:
            team_members = validated_data.pop(
                'team_members_registered', []
            )

            members_to_delete = EnterpriseMembers.objects.filter(
                enterprise=enterprise,
                user__isnull=False
            ).exclude(user__in=team_members)
            members_to_delete.delete()

            members_existing = EnterpriseMembers.objects.filter(
                enterprise=enterprise,
                user__isnull=False
            ).values_list('user__id', flat=True)
            members_to_add = [
                m for m in team_members if m not in members_existing
            ]

            for m in members_to_add:
                user = models.AppUser.objects.get(pk=m)
                enterprise.team_members_registered.add(
                    user,
                    through_defaults={
                        'type': EnterpriseMembers.USER_TYPE_MEDIATOR
                    }
                )
        super().update(enterprise, validated_data)
        return models.Enterprise.objects.get(pk=enterprise.pk)


class EnterpriseRegisterValidSerializer(serializers.Serializer):
    """ Сериализатор для проверки процесса регистрации предприятия """
    stage = serializers.ChoiceField(choices=['first', 'second'], required=True)


class EnterpriseRegisterValidFirstStepSerializer(
    AppUserRelatedRegisterSerializerMixin
):
    """ Простой сериализатор для проверки 1-го этапа регистрации предприятия. """
    username = serializers.ReadOnlyField()


class EnterpriseRegisterValidSecondStepSerializer(
    EnterpriseSerializer
):
    """ Простой сериализатор для проверки этапа регистрации enterprise 2d. """
    email = serializers.ReadOnlyField(source='user.email')

    def prepare_instance(self, attrs):
        """ Переопределен метод, чтобы заставить работать метод `instance.clean_user()`.
        Насколько этот сериализатор используется для регистрации предприятия
        проверка на 2d-шаге, у нас нет экземпляра "user" для
        текущее предприятие (потому что мы проверяем только поля 2d-шага, а
        "электронная почта" там отсутствует).
        Таким образом, проверка экземпляра `clean_user` прерывается в корпоративной модели.

        Чтобы исправить это, для пустого экземпляра "App User" установлено значение related
        экземпляр сериализатора.
        """
        instance = super().prepare_instance(attrs)
        instance.user = models.AppUser()
        return instance


class EnterpriseInviteMembersSerializer(EnterpriseSerializer):
    team_members = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        write_only=True
    )
    team_members_registered = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    team_members_data = serializers.SerializerMethodField()
    team_members_stats = serializers.SerializerMethodField()

    class Meta:
        model = models.Enterprise
        fields = (
            'team_members',
            'team_members_data',
            'team_members_registered',
            'team_members_registered_data',
            'team_members_stats',
        )
        read_only_fields = (
            'team_members_data',
            'team_members_registered_data',
        )

    def get_team_members_data(self, obj):
        members = []
        for m in obj.team_members_invited.all():
            data = MemberSerializer(m).data
            invite = EnterpriseMembers.objects.get(enterprise=obj, invitee=m)
            data.update({
                'state': invite.state,
                'type': invite.type
            })
            members.append(data)
        return members

    def get_team_members_stats(self, obj):
        mediator_count = len([
            m for m in obj.team_members_registered.all() if m.is_mediator
        ])
        pending_invites_count = obj.team_members_invited.count()
        seats_used = mediator_count + \
            pending_invites_count
        return {
            'mediator_count': mediator_count,
            'pending_invites_count': pending_invites_count,
            'seats_used': seats_used,
            'seats_available':
                int(obj.firm_size.title.split('-')[-1].split('+')[0])
        }

    def validate(self, data):
        """Check registration data"""
        team_members_registered = data.pop('team_members_registered', None)
        team_members = data.pop('team_members', None)
        data = super().validate(data)

        if team_members is not None:
            for m in team_members:
                if AppUser.objects.filter(email=m['email']).exists():
                    raise serializers.ValidationError(
                        "User with email '{}' already exist".format(m['email'])
                    )
            data.update({'team_members': team_members})
        if team_members_registered is not None:
            for user_id in team_members_registered:
                if not AppUser.objects.filter(pk=user_id).exists():
                    raise serializers.ValidationError(
                        "User with id={} does not exist".format(user_id)
                    )
                user = AppUser.objects.get(pk=user_id)
                if user.is_enterprise_admin:
                    raise serializers.ValidationError(
                        "Enterprise admin user(id={}) can't be invited".format(
                            user_id))
                if not user.is_mediator:
                    raise serializers.ValidationError(
                        "Client user(id={}) can't be member of team".format(
                            user_id))
            data.update({'team_members_registered': team_members_registered})
        return data

    def update(self, enterprise, validated_data):
        if 'team_members' in validated_data:
            team_members = validated_data.pop(
                'team_members', []
            )
            for obj in team_members:
                member, created = models.Member.objects.get_or_create(
                    email=obj['email']
                )
                if not models.EnterpriseMembers.objects.filter(
                    enterprise=enterprise,
                    invitee=member
                ).exists():
                    member._send_invitation(enterprise, obj['type'])
                    enterprise.team_members_invited.add(
                        member,
                        through_defaults={'type': obj['type']}
                    )
        if 'team_members_registered' in validated_data:
            team_members = validated_data.pop(
                'team_members_registered', []
            )

            members_existing = EnterpriseMembers.objects.filter(
                enterprise=enterprise,
                user__isnull=False
            ).values_list('user__id', flat=True)
            members_to_add = [
                m for m in team_members if m not in members_existing
            ]

            for m in members_to_add:
                user = models.AppUser.objects.get(pk=m)
                enterprise.team_members_registered.add(
                    user,
                    through_defaults={
                        'type': EnterpriseMembers.USER_TYPE_MEDIATOR
                    }
                )
        return models.Enterprise.objects.get(pk=enterprise.pk)
