from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from .utils import email_verification_created_handler

from ..models import VerificationCode

User = get_user_model()


class BaseAPIViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # deps
        email_verification_created_handler.connect()

    def tearDown(self) -> None:
        # deps
        email_verification_created_handler.disconnect()


class TestEmailVerificationCreateAPIView(BaseAPIViewTestCase):
    def test_create(self):
        response = self.client.post(
            reverse("EmailVerificationCreateAPIView"), {"email": "user@example.com"}
        )
        self.assertEqual(VerificationCode.objects.all().count(), 1)
        self.assertTrue(status.is_success(response.status_code))


class TestEmailVerificationVerifyAPIView(BaseAPIViewTestCase):
    def test_verify(self):
        vc = VerificationCode.objects.create(email="user@example.com")
        vc.set_code()

        response = self.client.post(
            reverse("EmailVerificationVerifyAPIView"),
            {"email": "user@example.com", "code": vc.code},
        )
        self.assertTrue(status.is_success(response.status_code))


class TestRegisterUserAPIView(BaseAPIViewTestCase):
    def setUp(self):
        super().setUp()
        self.inviter = User.objects.create_user(
            "john", "john@john.com", "johnpassword", role=User.Roles.TRUSTED
        )
        vc = VerificationCode.objects.create(email="user@example.com")
        vc.set_code()

        self.signature = vc.get_signature()

    def test_register(self):
        response = self.client.post(
            reverse("RegisterUserAPIView"),
            {
                "email": "user@example.com",
                "inviter": self.inviter.username,
                "password": "mycomplicatedpassword",
                "password_repeated": "mycomplicatedpassword",
                "signature": self.signature,
            },
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(User.objects.all().count(), 2)


class TestCompleteRegisterUserAPIView(BaseAPIViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            "1023942374092743", "john@john.com", "johnpassword"
        )

    def test_complete_register(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("CompleteRegisterUserAPIView"),
            {"username": "john", "full_name": "John Doe"},
        )
        self.assertTrue(status.is_success(response.status_code))
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "John Doe")
        self.assertEqual(self.user.username, "john")
        self.assertEqual(self.user.is_setup, True)


class TestCheckUserExistsAPIView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("john", "john@john.com", "johnpassword")

    def test_check(self):
        response = self.client.get(
            reverse("CheckUserExistsAPIView"),
            {
                "username": "user",
            },
        )

        self.assertTrue(status.is_success(response.status_code))

        self.assertFalse(response.data["exists"])

    def test_check_exists(self):
        response = self.client.get(
            reverse("CheckUserExistsAPIView"),
            {
                "username": "john",
            },
        )

        self.assertTrue(status.is_success(response.status_code))

        self.assertTrue(response.data["exists"])

    def test_check_when_no_username_provided(self):
        response = self.client.get(
            reverse("CheckUserExistsAPIView"),
            {},
        )
        self.assertFalse(status.is_success(response.status_code))
