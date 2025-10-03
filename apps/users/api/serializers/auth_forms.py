import os
from allauth.account import forms
from allauth.account.adapter import get_adapter
from constance import config


class ResetPasswordForm(forms.ResetPasswordForm):
    """Форма сброса пароля используется "Сериализатором подтверждения сброса пароля 
    пользователя приложения". Переопределено, чтобы вернуть ссылку на интерфейсную 
    часть и идентификатор пользователя как int. """

    def save(self, request, **kwargs):
        """ Переопределено, чтобы вернуть ссылку на интерфейсную часть и идентификатор 
        пользователя как int. """
        current_site = config.PROD_FRONTEND_LINK
        email = self.cleaned_data["email"]
        token_generator = kwargs.get(
            "token_generator", forms.default_token_generator
        )

        for user in self.users:
            temp_key = token_generator.make_token(user)

            # отправьте электронное письмо для сброса пароля
            url = config.PASSWORD_RESET_REDIRECT_LINK.format(
                domain=current_site, user_id=user.pk, token=temp_key
            )

            context = {
                "current_site": current_site,
                "username": user.first_name,
                "useremail": user.email,
                "password_reset_url": url,
                "request": request
            }

            get_adapter(request).send_mail(
                'account/email/password_reset_key',
                email,
                context
            )
        return self.cleaned_data["email"]
