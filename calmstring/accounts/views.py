from django.utils.translation import gettext_lazy as _
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from . import serializers, logic
from utils.api.permissions import IsNotAuthenticated
from utils.api.views import LogicAPIView
from .permissions import IsUserNotSetup
from rest_framework.response import Response
from rest_framework import status

from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.serializers import JWTSerializer
from django.contrib.auth import get_user_model


User = get_user_model()


class EmailVerificationCreateAPIView(LogicAPIView, CreateAPIView):
    """
    Send email confirmation to user
    """

    authentication_classes = ()
    permission_classes = [IsNotAuthenticated]
    serializer_class = serializers.EmailVerificationCreateSerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)

        email = self.serializer.validated_data["email"]

        try:
            logic.create_email_verification(email=email)
        except (
            logic.NonEmailCreateVerificationHandlersError,
            logic.EmailCreateVerificationHanlderError,
        ) as e:
            return Response(
                {self.DETAIL_KEY: str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        message = _("Verification code was sent to {}").format(email)
        return Response(
            {self.DETAIL_KEY: message},
            status=status.HTTP_201_CREATED,
        )


class EmailVerificationVerifyAPIView(LogicAPIView, CreateAPIView):
    """
    Verify email confirmation
    """

    authentication_classes = ()
    permission_classes = [IsNotAuthenticated]
    serializer_class = serializers.EmailVerificationVerifySerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)

        code = self.serializer.validated_data["code"]
        email = self.serializer.validated_data["email"]

        try:
            __, signature = logic.verify_email(email=email, code=code)
        except (
            logic.VerificationCodeObjectNotFoundError,
            logic.VerificationCodeInvalidError,
        ) as e:
            return Response(
                {self.DETAIL_KEY: str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        message = _("Email was verified")

        return Response(
            {self.DETAIL_KEY: message, "signature": signature},
            status=status.HTTP_201_CREATED,
        )


class RegisterUserAPIView(LogicAPIView, CreateAPIView):
    """Register new user account"""

    authentication_classes = ()
    permission_classes = [IsNotAuthenticated]
    serializer_class = serializers.RegisterUserSerializer

    def create(self, *args, **kwargs):
        super().create(*args, **kwargs)

        inviter = self.validated_data["inviter"]
        email = self.validated_data["email"]
        password = self.validated_data["password"]
        signature = self.validated_data["signature"]

        try:
            user = logic.register_user(inviter, email, password, signature)
        except (logic.InviterNotPermittedError, logic.InvalidSignatureError) as e:
            return Response(
                {self.DETAIL_KEY: str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        access_token, refresh_token = jwt_encode(user)
        data = {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        data = JWTSerializer(data, context=self.get_serializer_context()).data

        return Response(
            data,
            status=status.HTTP_201_CREATED,
        )


class CompleteRegisterUserAPIView(LogicAPIView, CreateAPIView):
    """Complete new user registration process"""

    permission_classes = [IsUserNotSetup]
    serializer_class = serializers.CompleteRegisterUserSerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)

        username = self.validated_data["username"]
        full_name = self.validated_data.get("full_name", None)

        try:
            logic.complete_register(request.user, username, full_name)
        except logic.UserAlreadySetupError as e:
            return Response(
                {self.DETAIL_KEY: str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {self.DETAIL_KEY: _("Successfully completed registration")},
            status=status.HTTP_201_CREATED,
        )


class CheckUserExistsAPIView(LogicAPIView, RetrieveAPIView):
    """Check if user with given username in query_params exists"""

    authentication_classes = ()
    permission_classes = [AllowAny]

    def retrieve(self, request):
        username = request.query_params.get("username")
        if not username:
            return Response(
                {self.DETAIL_KEY: _("Query param username is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {
                    self.DETAIL_KEY: _("Username is available"),
                    "exists": False,
                    "user": {"trusted": False},
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                self.DETAIL_KEY: _("Username is taken"),
                "exists": True,
                "user": {"trusted": user.has_role(user.Roles.TRUSTED)},
            },
            status=status.HTTP_200_OK,
        )
