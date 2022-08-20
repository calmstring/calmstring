from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from utils.exceptions import ValidationError, BaseException
from .models import VerificationCode
from . import exceptions, signals as accounts_signals
import logging

from utils.logic import signals_emiter


logger = logging.getLogger(__name__)

User = get_user_model()


"""Registration flow:

1. User enters email
2. User confirms email
3. User enters password
4. User provides username and optionaly full name

"""


class EmailCreateVerificationHanlderError(BaseException):
    pass


class NonEmailCreateVerificationHandlersError(BaseException):
    pass


class VerificationCodeObjectNotFoundError(BaseException):
    pass


class VerificationCodeInvalidError(BaseException):
    pass


class InviterNotPermittedError(BaseException):
    pass


class InvalidSignatureError(BaseException):
    pass


class UserAlreadySetupError(BaseException):
    pass


def create_email_verification(email: str, **kwargs):
    """Function generates a verification code, it's called when user prompt their email

    Raises:
        exceptions.EmailAlreadyAssignedError : if email is already assigned to another user
        exceptions.EmailCreateVerificationError: When there is not command handler for create_email_verification
        exceptions.EmailCreateVerificationError: When command hanlder thorws an exception

    Returns:
        bool: True or exceptions
    """

    user_email_exist = User.objects.filter(email=email).first()
    if user_email_exist:
        raise ValidationError(_("Email is already assigned to another user"))

    verification = VerificationCode.objects.create(email=email)
    verification.set_code()

    def internal_signals():
        accounts_signals.on_email_verification_created.send_robust(
            sender="accounts.on_email_verification_created",
            email=email,
            verification=verification,
        )

    signals_emiter(internal_signals, None, **kwargs)

    command_response = (
        accounts_signals.command_on_email_verification_created.send_robust(
            sender="accounts.on_email_verification_created",
            email=email,
            verification=verification,
        )
    )

    if not len(command_response):
        logger.critical("Command on_email_verification_created not executed")
        raise NonEmailCreateVerificationHandlersError(
            _("Error during email verification creation")
        )

    if isinstance(command_response[0][1], Exception):
        logger.critical("Command on_email_verification_created raised an exception")
        raise EmailCreateVerificationHanlderError(
            _("Error during email verification creation")
        )

    return True


def verify_email(email: str, code: str, **kwargs):
    """Function that verifies email address by gived code

    Raises:
        ValidationError: When not verification object found
        ValidationError: When code invalid or expired

    Returns:
        tuple: (verified,signature)
    """

    verification = VerificationCode.objects.filter(email=email, code=code).first()

    if not verification:
        raise VerificationCodeObjectNotFoundError(
            _("Verification code or email is invalid")
        )

    if not verification.is_valid(code):
        raise VerificationCodeInvalidError(_("Verification code is expired"))

    signature = verification.get_signature()

    def internal_signals():
        accounts_signals.on_email_verified.send_robust(
            sender="accounts.verify_email", verification=verification, email=email
        )

    signals_emiter(internal_signals, None, **kwargs)

    return (True, signature)


def register_user(inviter: User, email: str, password: str, signature: str, **kwargs):

    is_user_valid = inviter.has_role(User.Roles.TRUSTED)

    if not is_user_valid:
        raise InviterNotPermittedError(_("Inviter is not permitted"))

    is_signature_valid = VerificationCode.objects.signature_for_email_exists(
        email, signature
    )

    if not is_signature_valid:
        raise InvalidSignatureError(_("Email signature is invalid"))

    user = User.objects.create_user(
        username=User.generate_username(),
        email=email,
        password=password,
        inviter=inviter,
    )

    def internal_signals():
        accounts_signals.user_created.send_robust(
            sender="accounts.register_user", user=user
        )

    signals_emiter(internal_signals, None, **kwargs)

    return user


def complete_register(user: User, username: str, full_name: str = None, **kwargs):
    """Function that completes user registration.
    Sets username and full name if provided.

    Args:
        user (User): _description_
        username (str): _description_
        full_name (str, optional): _description_. Defaults to None.

    Raises:
        ValidationError: When accounts is setup

    Returns:
        User: updated user instance
    """

    if user.is_setup:
        raise UserAlreadySetupError(_("User is already setup"))

    user.username = username

    if full_name:
        user.full_name = full_name

    user.is_setup = True
    user.save()

    def internal_signals():
        accounts_signals.user_registered.send_robust(
            sender="accounts.complete_register", user=user
        )

    signals_emiter(internal_signals, None, **kwargs)

    return user


def change_user_role(editor: User, user: User, role: User.Roles, **kwargs):
    """Function that changes user role
    Editor can change a role only if he own the role.

    Args:
        editor (User): User who wants to change user role
        user (User): User to change role
        role (User.Roles): New role

    Raises:
        ValidationError: When editor is not permitted to change role

    Returns:
        User: user with new role
    """

    last_role = user.role

    if editor.has_role(role):
        user.role = role
        user.save()
    else:
        raise ValidationError(_("You are not permitted to set that role"))

    def internal_signals():
        accounts_signals.user_role_changed.send(
            sender="accounts.change_user_role", user=user
        )
        accounts_signals.user_edited.send(
            sender="accounts.change_user_role",
            user=user,
            last_role=last_role,
            new_role=role,
        )

    signals_emiter(internal_signals, None, **kwargs)

    return user
