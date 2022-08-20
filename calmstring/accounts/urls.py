from django.urls import include, path
from .views import (
    EmailVerificationCreateAPIView,
    EmailVerificationVerifyAPIView,
    RegisterUserAPIView,
    CompleteRegisterUserAPIView,
    CheckUserExistsAPIView,
)


email_verification_urlpatterns = [
    path(
        "create/",
        EmailVerificationCreateAPIView.as_view(),
        name="EmailVerificationCreateAPIView",
    ),
    path(
        "verify/",
        EmailVerificationVerifyAPIView.as_view(),
        name="EmailVerificationVerifyAPIView",
    ),
]

email_urlpatterns = [
    path(
        "verification/",
        include(email_verification_urlpatterns),
    )
]

register_urlpatterns = [
    path("", RegisterUserAPIView.as_view(), name="RegisterUserAPIView"),
    path(
        "complete/",
        CompleteRegisterUserAPIView.as_view(),
        name="CompleteRegisterUserAPIView",
    ),
]

user_urlpatterns = [
    path(
        "exists/",
        CheckUserExistsAPIView.as_view(),
        name="CheckUserExistsAPIView",
    ),
]

urlpatterns = [
    # password/reset/
    # password/reset/confirm/
    # login/
    # logout/
    # user/
    # password/change/
    # token/verify/
    # token/refresh/
    path("", include("dj_rest_auth.urls")),
    path("social/", include("accounts.social.urls")),
    path("email/", include(email_urlpatterns)),
    path("register/", include(register_urlpatterns)),
    path("user/", include(user_urlpatterns)),
]
