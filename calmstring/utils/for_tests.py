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
    self.administrative_user = User.objects.create_user(
        "administrative_user" "administrative_user@email.com",
        "administrative_user",
        role=User.Roles.ADMINISTRATIVE,
    )
    self.competitive_user = User.objects.create_user(
        "competitive_user",
        "competitive_user@email.com",
        "competitive_user",
        role=User.Roles.COMPETITIVE,
    )

    self.trusted_user = User.objects.create_user(
        "trusted_user",
        "trusted_user@email.com",
        "trusted_user",
        role=User.Roles.TRUSTED,
    )
    self.normal_user = User.objects.create_user(
        "normal_user", "normal_user@email.com", "normal_user", role=User.Roles.NORMAL
    )
    self.limited_user = User.objects.create_user(
        "limited_user",
        "limited_user@email.com",
        "limited_user",
        role=User.Roles.LIMITED,
    )


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
