from rest_framework import permissions


class IsNotAuthenticated(permissions.BasePermission):
    """
    Allows access only to unauthenticated users.
    """

    def has_permission(self, request, *args, **kwargs):
        return not request.user.is_authenticated

    def has_object_permission(self, request, *args, **kwargs):
        return not request.user.is_authenticated


class IsReadyOnly(permissions.BasePermission):
    def has_permission(self, request, *args, **kwargs):
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, *args, **kwargs):
        return request.method in permissions.SAFE_METHODS
