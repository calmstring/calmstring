from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from .serializers import CustomSocialLoginSerializer


class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    pass


class GoogleLoginView(
    SocialLoginView
):  # if you want to use Authorization Code Grant, use this
    adapter_class = CustomGoogleOAuth2Adapter
    # callback_url = CALLBACK_URL_YOU_SET_ON_GOOGLE
    client_class = OAuth2Client
    serializer_class = CustomSocialLoginSerializer

    authentication_classes = ()
    permission_classes = ()
