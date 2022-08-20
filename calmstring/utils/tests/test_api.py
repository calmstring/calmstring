from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from .models import KeyUuidModel, ModelWithKey

from ..api import permissions
from ..api.serializers import UUIDRelatedField


class TestIsNotAuthenticatedPermission(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.factory = RequestFactory()
        self.user = User.objects.create_user("user", "user@email.com", "Userpassword")

        self.permission = permissions.IsNotAuthenticated()

    def test_permission(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        permission = self.permission.has_permission(request)
        self.assertTrue(permission)

        object_permission = self.permission.has_object_permission(request)
        self.assertTrue(object_permission)

    def test_permission_when_user_is_authenticated(self):
        request = self.factory.get("/")
        request.user = self.user

        permission = self.permission.has_permission(request)
        self.assertFalse(permission)

        object_permission = self.permission.has_object_permission(request)
        self.assertFalse(object_permission)


class TestUUIDRelatedField(TestCase):
    def setUp(self):
        self.key1 = KeyUuidModel.objects.create(name="key1")
        self.key2 = KeyUuidModel.objects.create(name="key2")

        self.modelwithkey = ModelWithKey.objects.create(key=self.key1)

        class MySerializer(serializers.ModelSerializer):
            key = UUIDRelatedField(
                queryset=KeyUuidModel.objects.all(), uuid_field="uuid"
            )

            class Meta:
                model = ModelWithKey
                fields = ["key"]

        self.serializer = MySerializer

    def test_field(self):
        key1_uuid = self.key1.uuid
        serializer = self.serializer(data={"key": key1_uuid})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        self.assertEqual(validated_data["key"], self.key1)

    def test_invalid(self):
        serializers = self.serializer(data={"key": "invalid"})
        with self.assertRaises(Exception):
            serializers.is_valid(raise_exception=True)


class TestIsReadyOnlyPermission(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.factory = RequestFactory()
        self.user = User.objects.create_user("user", "user@email.com", "Userpassword")

        self.permission = permissions.IsReadyOnly()

    def test_permission(self):
        request = self.factory.get("/")
        request.user = self.user
        permission = self.permission.has_permission(request)
        self.assertTrue(permission)

    def _test_invalid(self, request):
        request.user = self.user
        permission = self.permission.has_permission(request)
        self.assertFalse(permission)

    def test_post(self):
        request = self.factory.post("/")
        self._test_invalid(request)

    def test_put(self):
        request = self.factory.put("/")
        self._test_invalid(request)

    def test_delete(self):
        request = self.factory.delete("/")
        self._test_invalid(request)

    def test_patch(self):
        request = self.factory.patch("/")
        self._test_invalid(request)
