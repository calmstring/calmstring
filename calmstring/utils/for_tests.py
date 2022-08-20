from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model


User = get_user_model()


def create_user(self, name, email=None, password=None, assign=True):
    _email = email
    if email is None:
        _email = name + "@" + name + ".com"
    _password = password
    if password is None:
        _password = name

    newUser = User.objects.create_user(name, _email, _password)

    if assign:
        setattr(self, name, newUser)

    return newUser


def setUp(self):
    self.superuser = User.objects.create_superuser(
        "superuser", "super@user.com", "superuser"
    )
    self.user = User.objects.create_user("user", "user@user.com", "user")


class TestCaseWithUsers(TestCase):
    def create_user(self, *args, **kwargs):
        return create_user(self, *args, **kwargs)

    def setUp(self):
        setUp(self)
        super().setUp()


class TransactionTestCaseWithUsers(TransactionTestCase):
    def create_user(self, *args, **kwargs):
        return create_user(self, *args, **kwargs)

    def setUp(self):
        setUp(self)
        super().setUp()
