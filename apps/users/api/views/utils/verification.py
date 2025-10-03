from django.contrib import messages
from django.http import HttpResponseRedirect

from allauth.account import signals
from allauth.account.adapter import get_adapter
from allauth.account.app_settings import EmailVerificationMethod
from allauth.account.models import EmailAddress
from allauth.account.utils import (
    get_login_redirect_url,
    send_email_confirmation,
    user_email,
)
from allauth.exceptions import ImmediateHttpResponse


def perform_login(request, user, email_verification,
                  redirect_url=None, signal_kwargs=None,
                  signup=False):
    """
    Keyword arguments:

    signup -- Indicates whether or not sending the
    email is essential (during signup), or if it can be skipped (e.g. in
    case email verification is optional and we are only logging in).
    """
    adapter = get_adapter(request)
    # Skip module checking `is_active` because this value is updated
    # by admin user
    # if not user.is_active:
    #     return adapter.respond_user_inactive(request, user)

    has_verified_email = EmailAddress.objects.filter(user=user,
                                                     verified=True).exists()
    if email_verification == EmailVerificationMethod.OPTIONAL:
        if not has_verified_email and signup:
            send_email_confirmation(request, user, signup=signup)
    elif email_verification == EmailVerificationMethod.MANDATORY:
        if not has_verified_email:
            send_email_confirmation(request, user, signup=signup)
            return adapter.respond_email_verification_sent(
                request, user)
    try:
        adapter.login(request, user)
        response = HttpResponseRedirect(
            get_login_redirect_url(request, redirect_url))

        if signal_kwargs is None:
            signal_kwargs = {}
        signals.user_logged_in.send(sender=user.__class__,
                                    request=request,
                                    response=response,
                                    user=user,
                                    **signal_kwargs)
        adapter.add_message(
            request,
            messages.SUCCESS,
            'account/messages/logged_in.txt',
            {'user': user})
    except ImmediateHttpResponse as e:
        response = e.response
    return response


def complete_signup(request, user, email_verification, success_url,
                    signal_kwargs=None):
    if signal_kwargs is None:
        signal_kwargs = {}
    signals.user_signed_up.send(sender=user.__class__,
                                request=request,
                                user=user,
                                **signal_kwargs)
    return perform_login(request, user,
                         email_verification=email_verification,
                         signup=True,
                         redirect_url=success_url,
                         signal_kwargs=signal_kwargs)


def resend_email_confirmation(request, user, signup=False):
    email_address = EmailAddress.objects.get_for_user(user, user_email(user))
    email_address.send_confirmation(request, signup=signup)
