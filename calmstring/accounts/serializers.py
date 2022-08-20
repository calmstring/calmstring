from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import VerificationCode

User = get_user_model()

from . import validators


class OmitCreateUpdate:
    def create(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass


class EmailVerificationCreateSerializer(serializers.ModelSerializer, OmitCreateUpdate):
    class Meta:
        model = User
        fields = ["email"]


class EmailVerificationVerifySerializer(serializers.ModelSerializer, OmitCreateUpdate):
    code = serializers.CharField()

    def validate_code(self, code):
        if len(code) != VerificationCode.CODE_LENGTH:
            raise serializers.ValidationError(
                _("Code needs to be {} digits".format(VerificationCode.CODE_LENGTH))
            )
        return code

    class Meta:
        model = User
        fields = ["email", "code"]


class RegistrationInviterSerializer(serializers.Serializer):
    inviter = serializers.CharField(help_text=_("User inviter username"))

    def validate_inviter(self, inviter):
        try:
            user_inviter = User.objects.get(username=inviter)
            validators.validate_inviter(user_inviter)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Provided inviter does not exist."))
        return user_inviter


class RegisterUserSerializer(
    serializers.ModelSerializer, OmitCreateUpdate, RegistrationInviterSerializer
):
    signature = serializers.CharField()
    password_repeated = serializers.CharField()

    def validate_password(self, password):
        validate_password(password)
        return password

    def validate(self, data):
        if data["password"] != data["password_repeated"]:
            raise serializers.ValidationError(_("Passwords must be the same"))

        return data

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_repeated",
            "inviter",
            "signature",
        ]


class CompleteRegisterUserSerializer(serializers.ModelSerializer, OmitCreateUpdate):
    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
        ]


class UserDetailsSerializer(serializers.ModelSerializer, OmitCreateUpdate):
    class Meta:
        model = User
        exclude = ["id", "password"]
