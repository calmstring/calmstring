from django.test import TestCase, override_settings
from django.db import transaction

from ..models import User, VerificationCode


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", "user@user.com")

    def assertHasRole(self, role):
        return self.assertTrue(self.user.has_role(role))

    def assertNotHasRole(self, role):
        return self.assertFalse(self.user.has_role(role))

    def test_has_role(self):
        self.user.role = User.Roles.LIMITED
        self.user.save()

        self.assertTrue(self.user.has_role(User.Roles.LIMITED))

        self.user.role = User.Roles.ADMINISTRATIVE
        self.user.save()

        self.assertHasRole(User.Roles.LIMITED)
        self.assertHasRole(User.Roles.NORMAL)
        self.assertHasRole(User.Roles.TRUSTED)
        self.assertHasRole(User.Roles.COMPETITIVE)
        self.assertHasRole(User.Roles.ADMINISTRATIVE)

        self.user.role = User.Roles.TRUSTED
        self.user.save()

        self.assertNotHasRole(User.Roles.COMPETITIVE)
        self.assertNotHasRole(User.Roles.ADMINISTRATIVE)

        self.assertHasRole(User.Roles.TRUSTED)

    def test_generate_username(self):
        # create few users
        import uuid

        users = [
            User(
                username=uuid.uuid4().hex,
                email=f"{uuid.uuid4().hex}@user.com",
                password="asdhfihweiochqwe",
            )
            for i in range(100)
        ]
        User.objects.bulk_create(users)

        random_username = User.generate_username()

        userN = User.objects.create_user(
            random_username, "userN@email.com", "asdhfoqawhuef"
        )
        self.assertEqual(userN.username, random_username)


class VerificationCodeTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "john", "john@test.com", "johnstrongpassword"
        )
        return super().setUp()

    def test_generate_code(self):

        code = VerificationCode.generate_code()
        for digit in code:
            self.assertTrue(digit in list("0123456789"))
        self.assertEqual(len(code), VerificationCode.CODE_LENGTH)

    def test_valid_code(self):
        vc = VerificationCode.objects.create(user=self.user)
        vc.set_code()
        code = vc.code
        self.assertTrue(vc.is_valid(code))

    def test_valid_code_with_email(self):
        vc = VerificationCode.objects.create(email=self.user.email)
        vc.set_code()
        code = vc.code
        self.assertTrue(vc.is_valid(code))

    def test_valid_code_manually_set(self):
        vc = VerificationCode.objects.create(user=self.user)
        vc.set_code("123456")
        self.assertTrue(vc.is_valid("123456"))

    def test_invalid_code(self):
        vc = VerificationCode.objects.create(user=self.user)
        vc.set_code("123456")
        self.assertFalse(vc.is_valid("65432"))

    @override_settings(CALMSTRING={"ACCOUNTS_CODE_EXPIRATION_TIME": -3600})
    def test_is_valid_expired_code(self):
        vc = VerificationCode.objects.create(user=self.user)
        vc.set_code("123456")
        self.assertFalse(vc.is_valid("123456"))

    @override_settings(CALMSTRING={"ACCOUNTS_CODE_EXPIRATION_TIME": 3600})
    def test_is_valid_not_expired_code(self):
        vc = VerificationCode.objects.create(user=self.user)
        vc.set_code("123456")
        self.assertTrue(vc.is_valid("123456"))

    def test_clear_code(self):
        vc = VerificationCode.objects.create(user=self.user)
        vc.set_code("123456")
        vc.clear_code()
        self.assertFalse(vc.is_valid("123456"))

    def test_email_signature(self):
        vc = VerificationCode.objects.create(email=self.user.email)
        vc.set_code()
        signature = vc.get_signature()
        self.assertTrue(vc.is_signature_valid(signature))

    def test_email_invalid_signature(self):
        vc = VerificationCode.objects.create(email=self.user.email)
        vc.set_code()
        self.assertFalse(vc.is_signature_valid("this is my random signature"))
        self.assertFalse(vc.is_signature_valid(vc.code))


class VerificationCodeManagerTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "john", "john@test.com", "johnstrongpassword"
        )
        self.vc1 = VerificationCode.objects.create(email=self.user.email)
        self.vc1.set_code()
        self.vc2 = VerificationCode.objects.create(email=self.user.email)
        self.vc2.set_code()

        return super().setUp()

    def test_signature_for_email_exists(self):
        vc1_email_signature = self.vc1.get_signature()

        exists = VerificationCode.objects.signature_for_email_exists(
            email=self.vc1.email, signature=vc1_email_signature
        )
        self.assertTrue(exists)

        vc2_email_signature = self.vc2.get_signature()
        exists = VerificationCode.objects.signature_for_email_exists(
            email=self.vc2.email, signature=vc2_email_signature
        )
        self.assertTrue(exists)

    def test_invalid_signature_for_email_exists(self):

        not_exists = VerificationCode.objects.signature_for_email_exists(
            email=self.vc1.email, signature="this is random signature"
        )
        self.assertFalse(not_exists)
