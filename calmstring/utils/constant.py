from django.db import models
from django.utils.translation import gettext_lazy as _


class AvailabilitiesBase(models.TextChoices):
    BUSY = "BUSY", _("Busy")
    FREE = "FREE", _("Free")
    UNAVAILABLE = "UNAVAILABLE", _("Unavailable")
    UNKNOWN = "UNKNOWN", _("Unknown")
