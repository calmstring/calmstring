from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model


User = get_user_model()


class IsUserNotSetup(BasePermission):
    """
    Allows access only to not setup users.
    """

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated and not request.user.is_setup

    def has_object_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated and not request.user.is_setup


class UserRoleBasePermission(BasePermission):
    role = None

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated and request.user.has_role(self.role)

    def has_object_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated and request.user.has_role(self.role)


class IsLimitedUser(UserRoleBasePermission):
    role = User.Roles.LIMITED


class IsNormalUser(UserRoleBasePermission):
    role = User.Roles.NORMAL


class IsTrustedUser(UserRoleBasePermission):
    role = User.Roles.TRUSTED


class IsCompetitiveUser(UserRoleBasePermission):
    role = User.Roles.COMPETITIVE


class IsAdministrativeUser(UserRoleBasePermission):
    role = User.Roles.ADMINISTRATIVE
