from django.db import models

from django.utils.translation import gettext_lazy as _

from utils.models import UUIDModel
from utils.constant import AvailabilitiesBase


# Create your models here.
class Room(UUIDModel):
    name = models.CharField(_("Name"), max_length=20)
    description = models.TextField(_("Description"))

    def __str__(self):
        return self.name

    @property
    def availability(self):
        try:
            return self.events_room.availability
        except Room.events_room.RelatedObjectDoesNotExist:

            return AvailabilitiesBase.UNKNOWN

    @property
    def events_room_uuid(self):
        try:
            return self.events_room.uuid
        except Room.events_room.RelatedObjectDoesNotExist:
            return None
