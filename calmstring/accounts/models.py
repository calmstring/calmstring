from django.db import models
from django.core import signing
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import random
import string
import uuid

from utils.models import UUIDModel

from . import conf

# Create your models here.
class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    """Just like normal user but with full_name insted of first_name last_name and roles"""

    class Roles(models.IntegerChoices):
        """
        Role based access with level inhertance
        e.g. ADMINISTRATIVE can all what TRUSTED can
        """

        LIMITED = 1, "User with just ready access"
        NORMAL = 2, "Normal user"
        TRUSTED = 3, "Trusted user"
        COMPETITIVE = 4, "Competitive user"
        ADMINISTRATIVE = 5, "Administrative user"

    role = models.PositiveSmallIntegerField(
        choices=Roles.choices, default=Roles.LIMITED
    )

    username_validator = UnicodeUsernameValidator()

    inviter = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, default=None
    )

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    full_name = models.CharField(_("User fullname"), max_length=50, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    is_setup = models.BooleanField(
        _("Is account setup"),
        default=False,
        help_text=_(
            "Designates whether this user has completed account setup. Got username and email"
        ),
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    @classmethod
    def generate_username(cls):
        """Generate random username as a hex uuid"""

        # is this code safe?
        random_username = uuid.uuid4().hex
        while cls.objects.filter(username=random_username).exists():
            random_username = uuid.uuid4().hex

        return random_username

    def has_role(self, role):
        """Check user got given or higher role"""
        return role <= self.role

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        default_permissions = ()


class VerificationCodeManager(models.Manager):
    def signature_for_email_exists(self, email: str, signature: str) -> bool:
        """Check if in db exists a VerificationCode object with given email and signature
        This method is only used when user is creating a new account

        Args:
            email (str): _description_
            signature (str): _description_

        Returns:
            bool: _description_
        """
        for vc in self.get_queryset().filter(email=email):
            if vc.is_signature_valid(signature):
                return True
        return False


class VerificationCode(UUIDModel):
    """Models used to store verification code"""

    CODE_LENGTH = 6

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, default=None
    )

    # if there is no user we wanna to hold email
    # instead (user is not confirming email on registration as a first step)
    email = models.EmailField(_("email address"), blank=True, null=True, default=None)

    code = models.CharField(max_length=CODE_LENGTH, null=True, default=None)
    expiration_date = models.DateTimeField(default=None, null=True, blank=True)

    def clear_code(self):
        self.code = None
        self.expiration_date = None
        self.save()

    def is_code_expired(self):
        try:
            return timezone.now() >= self.expiration_date
        except TypeError:
            return False

    @classmethod
    def generate_code(cls, length=CODE_LENGTH):
        printable = list(string.digits)
        random.shuffle(printable)

        random_code = random.choices(printable, k=length)

        return "".join(random_code)

    def set_code(self, code=None):
        if not code:
            code = self.generate_code()
        self.code = code
        self.expiration_date = timezone.now() + timedelta(
            seconds=conf.ACCOUNTS_CODE_EXPIRATION_TIME
        )
        self.save()

    signer = signing.Signer()

    def get_signature(self):
        value = self.signer.sign(self.code)
        return value.split(self.signer.sep)[1]

    def is_signature_valid(self, signature):
        value = f"{self.code}{self.signer.sep}{signature}"
        try:
            orginal = self.signer.unsign(value)
        except signing.BadSignature:
            return False

        return True

    def is_valid(self, code):

        return self.code and self.code == code and not self.is_code_expired()

    objects = VerificationCodeManager()
