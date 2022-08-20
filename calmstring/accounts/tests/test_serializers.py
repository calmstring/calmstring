from django.test import TestCase
from django.contrib.auth import get_user_model
from .. import serializers
from ..models import VerificationCode

User = get_user_model()


class TestEmailVerificationCreateSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("john", "john@john.com", "johnpassword")

    def test_serializer(self):
        serializer = serializers.EmailVerificationCreateSerializer(
            data={"email": "ala@matejko.com"}
        )
        self.assertTrue(serializer.is_valid())

        self.assertEqual(serializer.validated_data, {"email": "ala@matejko.com"})

    def test_invalid_email(self):
        serializer = serializers.EmailVerificationCreateSerializer(
            data={"email": "adfwerhu@@f"}
        )
        self.assertFalse(serializer.is_valid())

        serializer = serializers.EmailVerificationCreateSerializer(
            data={"email": self.user.email}
        )
        self.assertFalse(serializer.is_valid())


class TestEmailVerificationVerifySerializer(TestCase):
    def test_serializer(self):
        code = VerificationCode.generate_code()
        serializer = serializers.EmailVerificationVerifySerializer(
            data={"email": "some@email.com", "code": code}
        )
        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data, {"email": "some@email.com", "code": code}
        )

    def test_invalid_serializer(self):
        code = VerificationCode.generate_code()
        serializer = serializers.EmailVerificationVerifySerializer(
            data={"email": "some@email.com", "code": code + "q30r38"}
        )
        self.assertFalse(serializer.is_valid())


class TestRegisterUserSerializer(TestCase):
    def setUp(self):
        self.inviter = User.objects.create_user(
            "user", "user@user.com", "userpassword", role=User.Roles.TRUSTED
        )

    def test_register(self):
        serializer = serializers.RegisterUserSerializer(
            data={
                "email": "myemail@email.com",
                "username": "tomas",
                "password": "jaop324r9fn",
                "password_repeated": "jaop324r9fn",
                "inviter": self.inviter.username,
                "signature": "signature",  # can be invalid couse serializer it's not to check if sign. is valid
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_password(self):
        serializer = serializers.RegisterUserSerializer(
            data={
                "email": "myemail@email.com",
                "username": "tomas",
                "password": "fasdfh123!rhe",
                "password_repeated": "jaop324r9fn",
                "inviter": self.inviter.username,
                "signature": "signature",
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_weak_password(self):
        serializer = serializers.RegisterUserSerializer(
            data={
                "email": "myemail@email.com",
                "username": "tomas",
                "password": "tomas",
                "password_repeated": "tomas",
                "inviter": self.inviter.username,
                "signature": "signature",
            }
        )
        self.assertFalse(serializer.is_valid())


class TestCompleteRegisterUserSerializer(TestCase):
    def setUp(self) -> None:
        self.inviter = User.objects.create_user(
            "user", "user@user.com", "userpassword", role=User.Roles.TRUSTED
        )

    def test_serializer(self):
        serializer = serializers.CompleteRegisterUserSerializer(
            data={"username": "tomas", "full_name": "Tomas Aleksandrowicz"}
        )
        self.assertTrue(serializer.is_valid())

    def test_without_fullname(self):
        serializer = serializers.CompleteRegisterUserSerializer(
            data={"username": "tomas"}
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_username(self):
        serializer = serializers.CompleteRegisterUserSerializer(
            data={"username": "user"}
        )
        self.assertFalse(serializer.is_valid())


class TestUserDetailsSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "user",
            "user@user.com",
            "userpassword",
            role=User.Roles.TRUSTED,
            full_name="User Alan",
            is_setup=True,
        )

    def test_serializer(self):
        serializer = serializers.UserDetailsSerializer(self.user)

        self.assertNotIn("password", serializer.data.keys())
        self.assertNotIn("id", serializer.data.keys())
