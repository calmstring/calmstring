from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from rest_framework import serializers

from allauth.account import app_settings as allauth_settings
from allauth.socialaccount.helpers import complete_social_login
from requests.exceptions import HTTPError

from dj_rest_auth.registration.serializers import SocialLoginSerializer

from ..serializers import RegistrationInviterSerializer


class CustomSocialLoginSerializer(SocialLoginSerializer, RegistrationInviterSerializer):
    """Method used for custom Calmstring social login.
    Much of this method comes from dj_rest_auth SocialLoginSerializer
    """

    # override inviter to be optional
    inviter = serializers.CharField(
        help_text=_("User inviter username"), required=False, allow_blank=True
    )

    def create_user(self, request, sociallogin):
        u = sociallogin.user
        u.set_unusable_password()
        u.save()
        sociallogin.save(request)
        return u

    def complete_social_login(self, request, sociallogin):
        assert not sociallogin.is_existing
        sociallogin.lookup()

    def _validate_social(self, attrs):
        view = self.context.get("view")
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                _("View is not defined, pass it as a context variable"),
            )

        adapter_class = getattr(view, "adapter_class", None)
        if not adapter_class:
            raise serializers.ValidationError(_("Define adapter_class in view"))

        adapter = adapter_class(request)
        app = adapter.get_provider().get_app(request)

        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token

        access_token = attrs.get("access_token")
        code = attrs.get("code")
        # Case 1: We received the access_token
        if access_token:
            tokens_to_parse = {"access_token": access_token}
            token = access_token
            # For sign in with apple
            id_token = attrs.get("id_token")
            if id_token:
                tokens_to_parse["id_token"] = id_token

        # Case 2: We received the authorization code
        elif code:
            self.set_callback_url(view=view, adapter_class=adapter_class)
            self.client_class = getattr(view, "client_class", None)

            if not self.client_class:
                raise serializers.ValidationError(
                    _("Define client_class in view"),
                )

            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope,
                scope_delimiter=adapter.scope_delimiter,
                headers=adapter.headers,
                basic_auth=adapter.basic_auth,
            )
            token = client.get_access_token(code)
            access_token = token["access_token"]
            tokens_to_parse = {"access_token": access_token}

            # If available we add additional data to the dictionary
            for key in ["refresh_token", "id_token", adapter.expires_in_key]:
                if key in token:
                    tokens_to_parse[key] = token[key]
        else:
            raise serializers.ValidationError(
                _("Incorrect input. access_token or code is required."),
            )

        social_token = adapter.parse_token(tokens_to_parse)
        social_token.app = app

        try:
            login = self.get_social_login(adapter, app, social_token, token)
            self.complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))

        return login

    def _validate_email(self, login):
        # We have an account already signed up in a different flow
        # with the same email address: raise an exception.
        # This needs to be handled in the frontend. We can not just
        # link up the accounts due to security constraints
        if allauth_settings.UNIQUE_EMAIL:
            # Do we have an account already with this email address?
            account_exists = (
                get_user_model()
                .objects.filter(
                    email=login.user.email,
                )
                .exists()
            )
            if account_exists:
                raise serializers.ValidationError(
                    _("User is already registered with this e-mail address."),
                )

    def validate(self, attrs):

        login = self._validate_social(attrs)

        # Take care for creating or login in user

        if not login.is_existing:
            request = self._get_request()

            inviter = attrs.get("inviter")
            if not inviter:
                raise serializers.ValidationError("Inviter is required")

            login.user.inviter = inviter

            self._validate_email(login)

            # set username to random temporary value
            login.user.username = login.user.generate_username()

            self.create_user(request, login)

        attrs["user"] = login.account.user

        return attrs
