from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse


class CustomDefaultSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        full_name = first_name + " " + last_name

        user = sociallogin.user

        user.email = email
        user.full_name = full_name
        return user

    def pre_social_login(self, request, sociallogin):
        pass
