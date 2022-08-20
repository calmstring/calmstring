from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.sites.models import Site
import responses
import json
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework import status

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

User = get_user_model()


class TestGoogleAuth(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.inviter = User.objects.create_user(
            "john", "john@john.com", "johnpassword", role=User.Roles.TRUSTED
        )

        from allauth.socialaccount.models import SocialApp

        social_app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="123123123123",
            secret="567567567567",
        )

        site = Site.objects.get_current()
        social_app.sites.add(site)

    def get_fake_response_body(
        self,
        family_name="Penners",
        given_name="Raymond",
        name="Raymond Penners",
        email="raymond.penners@example.com",
        verified_email=True,
    ):
        return {
            "family_name": family_name,
            "name": name,
            "picture": "https://lh5.googleusercontent.com/photo.jpg",
            "locale": "nl",
            "gender": "male",
            "email": email,
            "link": "https://plus.google.com/108204268033311374519",
            "given_name": given_name,
            "id": "108204268033311374519",
            "verified_email": verified_email,
        }

    def mock_response(self, *args, **kwargs):
        responses.add(
            responses.GET,
            GoogleOAuth2Adapter.profile_url,
            body=json.dumps(self.get_fake_response_body(*args, **kwargs)),
            status=200,
            content_type="application/json",
        )

    @responses.activate
    def test_google_register(self):
        self.mock_response()
        response = self.client.post(
            reverse("google_login"),
            {"access_token": "abccorrect", "inviter": self.inviter.username},
        )
        self.assertTrue(status.is_success(response.status_code))

        user_count = User.objects.all().count()
        self.assertEqual(user_count, 2)

    @responses.activate
    def test_google_register_invalid(self):
        self.mock_response()

        # no inviter
        response = self.client.post(
            reverse("google_login"), {"access_token": "abccorrect"}
        )

        self.assertTrue(status.is_client_error(response.status_code))

    @responses.activate
    def test_google_login(self):
        # register
        self.mock_response()
        response = self.client.post(
            reverse("google_login"),
            {"access_token": "abccorrect", "inviter": self.inviter.username},
        )

        response = self.client.post(
            reverse("google_login"),
            {"access_token": "abccorrect"},
        )

        self.assertTrue(status.is_success(response.status_code))

    @responses.activate
    def test_google_register_invalid_email(self):
        self.mock_response()

        User.objects.create_user("tom", "raymond.penners@example.com", "johnpassword")

        response = self.client.post(
            reverse("google_login"),
            {"access_token": "abccorrect", "inviter": self.inviter.username},
        )
        self.assertTrue(status.is_client_error(response.status_code))

        user_count = User.objects.all().count()
        self.assertEqual(user_count, 2)
