from django.urls import path, re_path
from allauth.account import views as account_views
from allauth.socialaccount import views as social_views
from .api import views


urlpatterns = [
    path(
        'signup/',
        social_views.signup,
        name='socialaccount_signup',
    ),

    path(
        'confirm-email/<str:key>/',
        views.VerifyConfirmEmailRedirectView.as_view(),
        name="account_confirm_email",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        account_views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        'password/reset/key/done/',
        account_views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
]
