from django.db import models

from django.utils.translation import gettext_lazy as _

from utils.models import UUIDModel


# Create your models here.
class Room(UUIDModel):
    name = models.CharField(_("Name"), max_length=20)
    description = models.TextField(_("Description"))
