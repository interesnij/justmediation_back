from django.db.models import Q
from django.db.models.query import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_fsm import TransitionNotAllowed
from libs.django_fcm.api.exceptions import WrongTransitionException
from apps.business.api import filters
from apps.business.api.serializers.posted_matters import (
    PostedMattersByPracticeAreaSerializer,
    PostedMatterSerializer,
    ProposalSerializer,
)
from apps.business.models import PostedMatter, Proposal, MediatorRFP, ClientRFP, ContactForm
from apps.business.signals import (
    post_inactivated,
    post_reactivated,
    proposal_accepted,
    proposal_withdrawn,
)
from apps.core.api.views import CRUDViewSet
from apps.users.models.users import AppUser 
from apps.users.models.mediators import Mediator
from apps.users.models.extra import Speciality
from apps.forums.models import ForumPracticeAreas
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import uuid


class PostedMatterViewSet(CRUDViewSet):
    """
        Просмотр, установленный для просмотра опубликованных делов
        обеспечьте базовые операции CRUD.
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = PostedMatterSerializer
    queryset = PostedMatter.objects.all().select_related(
        'practice_area',
        'client__user',
        'currency',
        'client',
    ).prefetch_related(
        'proposals',
        'proposals__post',
        'proposals__mediator',
        'proposals__mediator__user',
        'proposals__currency'
    )
    filterset_class = filters.PostedMatterFilter
    search_fields = ('title', 'description')
    ordering_fields = (
        'created',
        'modified',
        'status_modified'
    )

    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        mediator_id = qp.get('mediator', None)
        proposal_id = qp.get('proposal', None)
        if proposal_id:
            return qs.filter(proposals__in=[proposal_id])
        if mediator_id:
            return qs.filter(
                Q(
                    proposals__mediator__in=[mediator_id],
                    status=PostedMatter.STATUS_INACTIVE
                ) | Q(status=PostedMatter.STATUS_ACTIVE)
            ).distinct()
        return qs

    @action(methods=['get'], detail=False)
    def practice_area_stats(self, request, *args, **kwargs):
        """ Просмотр статистики опубликованных дел для каждой области практики """

        practice_area_qs = ForumPracticeAreas.objects.all().prefetch_related(
            Prefetch(
                'posted_matter',
                queryset=PostedMatter.objects.filter(
                    status=PostedMatter.STATUS_ACTIVE
                ).order_by('-created')
            ),
            'posted_matter__currency',
            'posted_matter__client',
            'posted_matter__practice_area',
            'posted_matter__proposals',
            'posted_matter__proposals__mediator',
            'posted_matter__proposals__mediator__user',
            'posted_matter__proposals__currency',
        )
        search_text = request.query_params.get('search', '')
        practice_area_qs = practice_area_qs.filter(
            title__icontains=search_text
        )

        page = self.paginate_queryset(queryset=practice_area_qs)
        serializer = PostedMattersByPracticeAreaSerializer(
            page,
            many=True,
            context={"request": request}
        )

        ordering_fields = request.query_params.getlist('ordering', ['title'])

        data = serializer.data
        for field in ordering_fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            data = sorted(
                serializer.data,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )

        if page is not None:
            return self.paginator.get_paginated_response(data)

        return Response(
            data=data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def deactivate(self, request, *args, **kwargs):
        """ Деактивирует опубликованное дело """
        posted_matter = self.get_object()
        try:
            posted_matter.deactivate()
            posted_matter.save()
            post_inactivated.send(
                sender=PostedMatter, instance=self, user=request.user
            )
        except TransitionNotAllowed:
            raise WrongTransitionException
        serializer = self.serializer_class(posted_matter)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def reactivate(self, request, *args, **kwargs):
        """ Повторно активирует опубликованное дело """
        posted_matter = self.get_object()
        try:
            posted_matter.reactivate()
            posted_matter.save()
            post_reactivated.send(
                sender=PostedMatter, instance=self, user=request.user
            )
        except TransitionNotAllowed:
            raise WrongTransitionException
        serializer = self.serializer_class(posted_matter)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """ Отключить опубликованное дело """
        posted_matter = self.get_object()
        proposals = posted_matter.proposals.filter(
            status=Proposal.STATUS_ACCEPTED
        )
        if len(proposals) == 0:
            self.perform_destroy(posted_matter)
            posted_matter.proposals.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        for proposal in proposals:
            proposal.is_hidden_for_client = request.user.is_client
            proposal.is_hidden_for_mediator = request.user.is_mediator
            proposal.save()
        if request.user.is_client:
            posted_matter.is_hidden_for_client = True
            posted_matter.save()
        elif request.user.is_mediator:
            posted_matter.is_hidden_for_mediator = True
            posted_matter.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProposalViewSet(CRUDViewSet):
    """
        Вид, установленный для просмотра Proposal
        обеспечьте базовые операции CRUD.
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = ProposalSerializer
    search_fields = ('title', 'description')
    queryset = Proposal.objects.select_related(
        'mediator',
        'mediator__user',
        'currency'
    ).exclude(status=Proposal.STATUS_WITHDRAWN)
    filterset_class = filters.ProposalFilter
    ordering_fields = (
        'created',
        'modified',
        'status_modified'
    )

    @action(methods=['post'], detail=True)
    def withdraw(self, request, *args, **kwargs):
        """ Представление для отзыва предложения адвоката. """
        proposal = self.get_object()
        proposal.status = Proposal.STATUS_WITHDRAWN
        proposal.status_modified = timezone.now()
        proposal.save()
        proposal_withdrawn.send(
            sender=Proposal, instance=proposal, user=request.user
        )
        serializer = self.serializer_class(proposal)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def accept(self, request, *args, **kwargs):
        """ Представление для принятия предложения. """
        proposal = self.get_object()
        if proposal.post.status == PostedMatter.STATUS_INACTIVE:
            return Response(
                data={"detail": "Can not accept this proposal"},
                status=status.HTTP_400_BAD_REQUEST
            )
        proposal.status = Proposal.STATUS_ACCEPTED
        proposal.status_modified = timezone.now()
        proposal.save()
        PostedMatter.objects.filter(pk=proposal.post.pk).update(
            status=PostedMatter.STATUS_INACTIVE
        )
        proposal_accepted.send(
            sender=Proposal, instance=proposal, user=request.user
        )
        serializer = self.serializer_class(proposal)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def revoke(self, request, *args, **kwargs):
        """ Представление для отозыва предложение. """
        proposal = self.get_object()
        proposal.status = Proposal.STATUS_REVOKED
        proposal.status_modified = timezone.now()
        proposal.save()
        PostedMatter.objects.filter(pk=proposal.post.pk).update(
            status=PostedMatter.STATUS_ACTIVE
        )
        serializer = self.serializer_class(proposal)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

class ClientRFPViewSet(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ClientRFPViewSet, self).dispatch(request, *args, **kwargs)
    
    def create_mediator(self, first_name, last_name, email, phone):
        if not first_name or not last_name or not email:
            return None
        if not AppUser.objects.filter(email=email).exists():
            password = str(uuid.uuid4())
            user = AppUser.objects.create_user(
                uuid = password,
                password = password,
                first_name = first_name,
                middle_name = None,
                last_name = last_name,
                email = email,
                phone = phone,
                onboarding = True,
                is_active = True,
            )

            user.set_password(password)
            user.is_active = True
            user.is_free_subscription = True
            user.save()

            Mediator.objects.create(
                user = user,
                license_info = "empty",
                verification_status = "approved",
            )

            return [user, password]
        return [None, None]

    
    def post(self, request, *args, **kwargs):
        inquiries_first_name = request.POST.get('inquiries_first_name')
        inquiries_last_name = request.POST.get('inquiries_last_name')
        inquiries_email = request.POST.get('inquiries_email')
        inquiries_phone = request.POST.get('inquiries_phone')

        dedlain_first_name = request.POST.get('dedlain_first_name')
        dedlain_last_name = request.POST.get('dedlain_last_name')
        dedlain_email = request.POST.get('dedlain_email')
        dedlain_phone = request.POST.get('dedlain_phone')
        print("inquiries_first_name ", inquiries_first_name)
        print("dedlain_first_name ", dedlain_first_name)


        [inquiries_user, password] = self.create_mediator(inquiries_first_name, inquiries_last_name, inquiries_email, inquiries_phone)
        dedlain_user = self.create_mediator(dedlain_first_name, dedlain_last_name, dedlain_email, dedlain_phone)[0]
        open_submission = request.POST.get('open_submission')
        close_submission = request.POST.get('close_submission')
        dedline_open_submission = request.POST.get('dedline_open_submission')
        dedline_close_submission = request.POST.get('dedline_close_submission')
        individ_date = request.POST.get('individ_date')
        documents = request.POST.get('documents')
        description = request.POST.get('description')
        potencial_client_conflicts = request.POST.get('potencial_client_conflicts')
        company_or_duns = request.POST.get('company_or_duns')
        who_can_respond_to_rfp = request.POST.get('who_can_respond_to_rfp')
        responsible_mediator_qualifications = request.POST.get('responsible_mediator_qualifications')
        location_license_admissions = request.POST.get('location_license_admissions')
        anticipated_period = request.POST.get('anticipated_period')
        range_of_packages = request.POST.get('range_of_packages')
        expected_extention = request.POST.get('expected_extention')
        mediators_count = request.POST.get('mediators_count')
        hourly_fee_enabled = request.POST.get('hourly_fee_enabled') == 'true'
        success_fee_enabled = request.POST.get('success_fee_enabled') == 'true'
        sliding_scale_fee_enabled = request.POST.get('sliding_scale_fee_enabled') == 'true'
        litigation_funding_enabled = request.POST.get('litigation_funding_enabled') == 'true'
        retainer_fee_enabled = request.POST.get('retainer_fee_enabled') == 'true'
        subscription_fee_enabled = request.POST.get('subscription_fee_enabled') == 'true'
        bended_rate_enabled = request.POST.get('bended_rate_enabled') == 'true'
        hybrid_fee_enabled = request.POST.get('hybrid_fee_enabled') == 'true'
        contingency_fee_enabled = request.POST.get('contingency_fee_enabled') == 'true'
        caped_fee_enabled = request.POST.get('caped_fee_enabled') == 'true'
        proect_bases_fee_enabled = request.POST.get('proect_bases_fee_enabled') == 'true'
        print("documents ", documents)

        if open_submission == "":
            open_submission = None
        if close_submission == "":
            close_submission = None
        if dedline_open_submission == "":
            dedline_open_submission = None
        if dedline_close_submission == "":
            dedline_close_submission = None
        if individ_date == "":
            individ_date = None
        
        new_post = ClientRFP.objects.create(
            open_submission=open_submission,
            close_submission=close_submission,
            dedline_open_submission=dedline_open_submission,
            dedline_close_submission=dedline_close_submission,
            individ_date=individ_date,
            documents=documents,
            description=description,

            potencial_client_conflicts=potencial_client_conflicts,
            company_or_duns=company_or_duns,
            who_can_respond_to_rfp=who_can_respond_to_rfp,
            responsible_mediator_qualifications=responsible_mediator_qualifications,
            location_license_admissions=location_license_admissions,
            anticipated_period=anticipated_period,
            range_of_packages=range_of_packages,
            expected_extention=expected_extention,
            mediators_count=mediators_count,
            inquiries_user=inquiries_user,
            dedlain_user=dedlain_user,
            hourly_fee_enabled=hourly_fee_enabled,
            success_fee_enabled=success_fee_enabled,
            sliding_scale_fee_enabled=sliding_scale_fee_enabled,
            litigation_funding_enabled=litigation_funding_enabled,
            retainer_fee_enabled=retainer_fee_enabled,
            subscription_fee_enabled=subscription_fee_enabled,
            bended_rate_enabled=bended_rate_enabled,
            hybrid_fee_enabled=hybrid_fee_enabled,
            contingency_fee_enabled=contingency_fee_enabled,
            caped_fee_enabled=caped_fee_enabled,
            proect_bases_fee_enabled=proect_bases_fee_enabled,
        )
        specialities_list = request.POST.getlist('specialities')
        for i in specialities_list:
            spec = Speciality.objects.get(id=i)
            new_post.specialities.add(spec)

        scope_of_services_list = request.POST.getlist('scope_of_services')
        for i in scope_of_services_list:
            spec = Speciality.objects.get(id=i)
            new_post.scope_of_services.add(spec)
        
        mediators_specialities_list = request.POST.getlist('mediators_specialities')
        for i in mediators_specialities_list:
            spec = Speciality.objects.get(id=i)
            new_post.mediators_specialities.add(spec)
        
        license_admissions_list = request.POST.getlist('license_admissions')
        for i in license_admissions_list:
            spec = Speciality.objects.get(id=i)
            new_post.license_admissions.add(spec)
        
        mediators_email_list = request.POST.getlist('new_mediator_email')
        mediators_forloop = 0
        for i in mediators_email_list:
            try:
                mediators_first_name_list = request.POST.getlist('new_mediator_first_name')
                mediators_last_name_list = request.POST.getlist('new_mediator_last_name')
                user = self.create_mediator(mediators_first_name_list[mediators_forloop], mediators_last_name_list[mediators_forloop], i, None)[0]
                new_post.mediators.add(user)
                mediators_forloop += 1
            except:
                continue

        return JsonResponse({'password':password})

class ContactFormViewSet(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ContactFormViewSet, self).dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        new_post = ContactForm.objects.create(
            name=name,
            email=email,
            message=message,
        )

        return JsonResponse({'id':new_post.id})
    

class MediatorRFPViewSet(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(MediatorRFPViewSet, self).dispatch(request, *args, **kwargs)
    
    def create_mediator(self, first_name, last_name, email, phone):
        if not first_name or not last_name or not email:
            return None
        if not AppUser.objects.filter(email=email).exists():
            password = str(uuid.uuid4())
            user = AppUser.objects.create_user(
                uuid = password,
                password = password,
                first_name = first_name,
                middle_name = None,
                last_name = last_name,
                email = email,
                phone = phone,
                onboarding = True,
                is_active = True,
            )

            user.set_password(password)
            user.is_active = True
            user.is_free_subscription = True
            user.save()

            Mediator.objects.create(
                user = user,
                license_info = "empty",
                verification_status = "approved",
            )

            return [user, password]
        return [None, None]

    def post(self, request, *args, **kwargs):
        inquiries_first_name = request.POST.get('inquiries_first_name')
        inquiries_last_name = request.POST.get('inquiries_last_name')
        inquiries_email = request.POST.get('inquiries_email')
        inquiries_phone = request.POST.get('inquiries_phone')

        dedlain_first_name = request.POST.get('dedlain_first_name')
        dedlain_last_name = request.POST.get('dedlain_last_name')
        dedlain_email = request.POST.get('dedlain_email')
        dedlain_phone = request.POST.get('dedlain_phone')

        [inquiries_user, password] = self.create_mediator(inquiries_first_name, inquiries_last_name, inquiries_email, inquiries_phone)
        dedlain_user = self.create_mediator(dedlain_first_name, dedlain_last_name, dedlain_email, dedlain_phone)[0]
        open_submission = request.POST.get('open_submission')
        close_submission = request.POST.get('close_submission')
        dedline_open_submission = request.POST.get('dedline_open_submission')
        dedline_close_submission = request.POST.get('dedline_close_submission')
        documents = request.POST.get('documents')
        description = request.POST.get('description')
        mediators_count = request.POST.get('mediators_count')
        location_license_admissions = request.POST.get('location_license_admissions')
        location = request.POST.get('location')
        no_conflict = request.POST.get('no_conflict') == 'true'
        review_draft_negatiate = request.POST.get('review_draft_negatiate') == 'true'
        advise_individual_labor = request.POST.get('advise_individual_labor') == 'true'
        advise_individual = request.POST.get('advise_individual') == 'true'
        mediator_can_accept_responsibility = request.POST.get('mediator_can_accept_responsibility') == 'true'
        anticipated_contract_period_enabled = request.POST.get('anticipated_contract_period_enabled') == 'true'
        fee_structure_enabled = request.POST.get('fee_structure_enabled') == 'true'

        if open_submission == "":
            open_submission = None
        if close_submission == "":
            close_submission = None
        if dedline_open_submission == "":
            dedline_open_submission = None
        if dedline_close_submission == "":
            dedline_close_submission = None
        
        new_post = MediatorRFP.objects.create(
            open_submission=open_submission,
            close_submission=close_submission,
            dedline_open_submission=dedline_open_submission,
            dedline_close_submission=dedline_close_submission,
            documents=documents,
            description=description,
            mediators_count=mediators_count,
            location_license_admissions=location_license_admissions,
            location=location,
            no_conflict=no_conflict,
            review_draft_negatiate=review_draft_negatiate,
            advise_individual_labor=advise_individual_labor,
            advise_individual=advise_individual,
            inquiries_user=inquiries_user,
            dedlain_user=dedlain_user,
            mediator_can_accept_responsibility=mediator_can_accept_responsibility,
            anticipated_contract_period_enabled=anticipated_contract_period_enabled,
            fee_structure_enabled=fee_structure_enabled,
        )

        specialities_list = request.POST.getlist('specialities')
        for i in specialities_list:
            spec = Speciality.objects.get(id=i)
            new_post.specialities.add(spec)

        scope_of_services_list = request.POST.getlist('scope_of_services')
        for i in scope_of_services_list:
            spec = Speciality.objects.get(id=i)
            new_post.scope_of_services.add(spec)
        
        mediators_email_list = request.POST.getlist('new_mediator_email')
        mediators_forloop = 0
        for i in mediators_email_list:
            try:
                mediators_first_name_list = request.POST.getlist('new_mediator_first_name')
                mediators_last_name_list = request.POST.getlist('new_mediator_last_name')
                user = self.create_mediator(mediators_first_name_list[mediators_forloop], mediators_last_name_list[mediators_forloop], i, None)[0]
                new_post.mediators.add(user)
                mediators_forloop += 1
            except:
                continue

        respond_mediators_email_list = request.POST.getlist('respond_mediator_email')
        mediators_forloop = 0
        for i in respond_mediators_email_list:
            try:
                mediators_first_name_list = request.POST.getlist('respond_mediator_first_name')
                mediators_last_name_list = request.POST.getlist('respond_mediator_last_name')
                user = self.create_mediator(mediators_first_name_list[mediators_forloop], mediators_last_name_list[mediators_forloop], i, None)[0]
                new_post.respond_mediators.add(user)
                mediators_forloop += 1
            except:
                continue

        return JsonResponse({'password': password})