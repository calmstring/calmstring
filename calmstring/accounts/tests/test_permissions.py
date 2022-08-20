from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .. import permissions


class TestIsUserNotSetup(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.factory = RequestFactory()
        self.user = User.objects.create_user("user", "user@email.com", "Userpassword")

        self.permission = permissions.IsUserNotSetup()

        self.request = self.factory.get("/")

    def test_when_user_not_setup(self):
        self.request.user = self.user
        self.assertTrue(self.permission.has_permission(self.request))
        self.assertTrue(self.permission.has_object_permission(self.request))

    def test_when_user_is_setup(self):
        self.user.is_setup = True
        self.user.save()
        self.request.user = self.user
        self.assertFalse(self.permission.has_permission(self.request))
        self.assertFalse(self.permission.has_object_permission(self.request))

    def test_when_user_not_authenticated(self):
        self.request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(self.request))
        self.assertFalse(self.permission.has_object_permission(self.request))


class TestUserRoleBasePermission(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.factory = RequestFactory()
        self.user = User.objects.create_user("user", "user@email.com", "Userpassword")

        class MyPermissions(permissions.UserRoleBasePermission):
            role = User.Roles.NORMAL

        self.permission = MyPermissions()

        self.request = self.factory.get("/")

    def test_when_limited(self):
        self.user.role = self.user.Roles.LIMITED
        self.user.save()

        self.request.user = self.user
        self.assertFalse(self.permission.has_permission(self.request))

    def test_when_normal(self):
        self.user.role = self.user.Roles.NORMAL
        self.user.save()

        self.request.user = self.user
        self.assertTrue(self.permission.has_permission(self.request))

    def test_when_higher_than_normal(self):
        self.user.role = self.user.Roles.COMPETITIVE
        self.user.save()

        self.request.user = self.user
        self.assertTrue(self.permission.has_permission(self.request))
