import os
from django.http import HttpResponseRedirect
from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter
from constance import config
from apps.users.models import AppUser
import requests
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    """Адаптер для хранения дополнительных полей при регистрации.

    Измените его, если вам нужны пользовательские поля, сохраненные при регистрации пользователя.
    http://django-allauth.readthedocs.org/en/latest/advanced.html#creating-and-populating-user-instances

    """

    def save_user(self, request, user, form, **kwargs):
        """ Постоянный пользователь.
        Аргументы: 
            user (users.AppUser): пустой экземпляр AppUser
            form (Custom RegisterSerializer): Сериализатор, заполненный значениями
        """
        user.avatar = form.cleaned_data.get('avatar', '')
        user.phone = form.cleaned_data.get('phone', None)
        return super().save_user(request, user, form)

    def respond_email_verification_sent(self, request, user):
        return HttpResponseRedirect(
            reverse("v1:account_email_verification_sent")
        )

    def format_email_subject(self, subject):
        return subject


    def send_rfp_mail(self, user, password):
        ctx = {
            "user": user,
            "current_site": "https://app.justmediation.com/",
            "password": password,
        }
        email_template = 'account/email/rfp_email'
        self.send_mail(email_template, 'tech@justmediation.com', ctx)
    
    def send_new_mediator_mail(self, user, password):
        ctx = {
            "user": user,
            "current_site": "https://app.justmediation.com/",
            "password": password,
        }
        email_template = 'account/email/new_mediator_email'
        self.send_mail(email_template, 'tech@justmediation.com', ctx)


    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = config.PROD_FRONTEND_LINK
        activate_url = self.get_email_confirmation_url(
            request,
            emailconfirmation)
        user = AppUser.objects.get(email=emailconfirmation.email_address.email)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "is_client": user.is_client,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
            "user_key": emailconfirmation.email_address.user.uuid,
        }
        if signup:
            email_template = 'account/email/email_confirmation_signup'
        else:
            email_template = 'account/email/email_confirmation'
        if emailconfirmation.email_address.user.is_subscribed:
            self.send_mail(
                email_template,
                emailconfirmation.email_address.email,
                ctx
            )
            if user.is_client:
                activate_url = "https://backend.justmediation.com/admin/users/client/" + str(user.id) + "/change/"
                text = "New client " + user.full_name + " has completed registration."
                user_types = 1
                self.send_mail( 
                    'notifications/users/new_user_registered/email',
                    'tech@justmediation.com',
                    {
                        "instance": user,
                        "current_site": current_site,
                        "activate_url": activate_url,
                        "text": text,
                    }
                )
            elif user.is_mediator:
                user_types = 2
            #    activate_url = "https://backend.justmediation.com/admin/users/mediator/" + str(user.id) + "/change/"
            #    text = "New mediator " + user.full_name + " has completed registration and waiting for your approval."
            elif user.is_enterprise_admin:
                user_types = 4
            #    _pk = models.Enterprise.objects.get(user_id=user.id)
            #    activate_url = "https://backend.justmediation.com/admin/users/enterprise/" + str(_pk) + "/change/"
            #    text = "New enterprise admin " + user.full_name + " has completed registration and waiting for your approval."
            else:
                user_types = 1
            #    activate_url = "https://backend.justmediation.com/admin/"
            #    text = "New app user " + user.full_name + " has completed registration."
            if settings.F_DOMAIN != "":
                requests.post(settings.F_DOMAIN + 'create_user', json={
                    "token": settings.OUT_TOKEN,
                    "user_id": user.id,
                    "types": user_types
                })


