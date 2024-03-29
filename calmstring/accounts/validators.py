from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_inviter(inviter):
    if not inviter.has_role(inviter.Roles.TRUSTED):
        raise ValidationError(_("Inviter is not permitted"))
