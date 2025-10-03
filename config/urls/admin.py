from django.contrib import admin
from django.urls import path
from apps.business.api.views import ClientRFPViewSet, MediatorRFPViewSet, ContactFormViewSet
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from apps.users import models


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
	
urlpatterns = [
    path('adminka/', admin.site.urls),
    path('contact_form/', ContactFormViewSet.as_view()),
    path('client_rfp/', ClientRFPViewSet.as_view()),
    path('mediator_rfp/', MediatorRFPViewSet.as_view()),
    path('dashboard/', DashboardView.as_view()),
	path('admin/', Dashboard2View.as_view()),
]
