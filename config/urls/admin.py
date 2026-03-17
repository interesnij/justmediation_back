from django.contrib import admin
from django.urls import path
from apps.business.api.views import ClientRFPViewSet, MediatorRFPViewSet, ContactFormViewSet
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from apps.users import models
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class DashboardView(TemplateView):
	template_name="dashboard/dashboard.html"
	
	def get_context_data(self,**kwargs):
		mediator_stats = models.Mediator.objects.aggregate_count_stats()
		clients_count = models.Client.objects.all().count() + 8000
		context = super(DashboardView,self).get_context_data(**kwargs)
		context["verified_count"] = mediator_stats['verified_count'] + 5000
		context["not_verified_count"] = mediator_stats['not_verified_count']
		context["mediators_total_count"] = mediator_stats['total_count'] + 5000
		context["clients_count"] = clients_count
		context["total_count"] = mediator_stats['total_count'] + clients_count + 5000
		return context

class Dashboard2View(ListView):
	template_name="dashboard/dashboard2.html"
	paginate_by = 20
	
	def get_context_data(self,**kwargs):
		mediator_stats = models.Mediator.objects.aggregate_count_stats()
		clients_count = models.Client.objects.all().count() + 8000
		context = super(Dashboard2View,self).get_context_data(**kwargs)
		context["verified_count"] = mediator_stats['verified_count']
		context["not_verified_count"] = mediator_stats['not_verified_count']
		context["mediators_total_count"] = mediator_stats['total_count']
		context["clients_count"] = clients_count
		context["total_count"] = mediator_stats['total_count'] + clients_count
		return context
	
	def get_queryset(self):
		list = models.AppUser.objects.filter(mediator__have_speciality=True)
		return list

from apps.users.models.users import AppUser
from apps.users.models.mediators import Mediator
from apps.users.models.clients import Client
from apps.users.models.mediator_links import MediatorRegistrationAttachment
from apps.users.models.enterprise import Enterprise
from apps.users.models.extra import Jurisdiction, Speciality
def create_attorney(
            role, first_name, last_name, password, phone, email, license_info, firm_name,
            bio, specialities, files, user_role):
        if AppUser.objects.filter(email=email).exists():
            print(" user exists!")
        user = AppUser.objects.create_user(
            type = role,
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
        new_user = Mediator.objects.create(
            user = user,
            license_info = license_info,
            firm_name = firm_name,
            verification_status = "approved",
            biography = bio,
        )
        for i in files:
              MediatorRegistrationAttachment.objects.create(mediator=new_user, attachment=i)

        for m in specialities:
            if Speciality.objects.filter(title=m).exists():
                spec = Speciality.objects.get(title=m.strip())
            else:
                spec = Speciality.objects.create(title=m.strip())
            user.specialities.add(spec)
        
        if firm_name:
            new_enterprise = Enterprise.objects.create(
                user = user,
                role = user_role,
                firm_name = firm_name,
                firm_size = 1,
            )
      
class AttorneyCreateView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AttorneyCreateView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("request files ", request.FILES.getlist('attachments'))
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        firm_name = request.POST.get("firm_name")
        biography = request.POST.get("bio")
        specialities = request.POST.getlist("practice_type")
        files = request.FILES.getlist('attachments')
        create_attorney("attorney", first_name, last_name, password, phone, email, "empty", firm_name, biography, specialities, files, "")
        return JsonResponse({'resp':'ok'})
    
class MediatorCreateView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(MediatorCreateView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("request files ", request.FILES.getlist('attachments'))
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        firm_name = request.POST.get("firm_name")
        biography = request.POST.get("bio")
        specialities = request.POST.getlist("practice_type")
        license_info = request.POST.get('certifications')
        create_attorney("mediator", first_name, last_name, password, phone, email, license_info, firm_name, biography, specialities, [], "")
        return JsonResponse({'resp':'ok'})

class LawFirmCreateView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LawFirmCreateView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("request files ", request.FILES.getlist('attachments'))
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        firm_name = request.POST.get("firm_name")
        biography = request.POST.get("bio")
        specialities = request.POST.getlist("practice_area")
        files = request.FILES.getlist('attachments')
        license_info = request.POST.get('certifications')
        user_role = request.POST.get("user_role")
        create_attorney("attorney", first_name, last_name, password, phone, email, license_info, firm_name, biography, specialities, files, user_role)
        return JsonResponse({'resp':'ok'})

class CorporateCreateView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CorporateCreateView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("request files ", request.FILES.getlist('attachments'))
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("direct_phone")
        password = request.POST.get("password")
        firm_name = request.POST.get("firm_name")
        files = request.FILES.getlist('attachments')
        job = request.POST.get('contact_title')
        if AppUser.objects.filter(email=email).exists():
            print(" user exists!")
        user = AppUser.objects.create_user(
            type = "Corporate",
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
        new_user = Client.objects.create(
            user = user,
            client_type = "firm",
            organization_name = firm_name,
            job = job,
        )
        for i in files:
              MediatorRegistrationAttachment.objects.create(mediator=new_user, attachment=i)
        return JsonResponse({'resp':'ok'})
    
urlpatterns = [
    path('adminka/', admin.site.urls),
    path('contact_form/', ContactFormViewSet.as_view()),
    path('client_rfp/', ClientRFPViewSet.as_view()),
    path('mediator_rfp/', MediatorRFPViewSet.as_view()),
    path('dashboard/', DashboardView.as_view()),
	path('admin/', Dashboard2View.as_view()),
	path('attorney_create/', AttorneyCreateView.as_view()),
	path('law_firm_create/', LawFirmCreateView.as_view()),
	path('mediator_create/', MediatorCreateView.as_view()),
	path('corporate_create/', CorporateCreateView.as_view()),
]
