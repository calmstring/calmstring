from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from recurrence.fields import RecurrenceField

from utils.models import UUIDModel, TimestampsModel

from datetime import datetime


class AvailabilitiesBase(models.TextChoices):
    BUSY = "BUSY", _("Busy")
    FREE = "FREE", _("Free")
    UNAVAILABLE = "UNAVAILABLE", _("Unavailable")
    UNKNOWN = "UNKNOWN", _("Unknown")


# Create your models here.
class Room(UUIDModel):
    class Availabilities(models.TextChoices):
        BUSY = AvailabilitiesBase.BUSY.value, AvailabilitiesBase.BUSY.label
        FREE = AvailabilitiesBase.FREE.value, AvailabilitiesBase.FREE.label
        UNAVAILABLE = (
            AvailabilitiesBase.UNAVAILABLE.value,
            AvailabilitiesBase.UNAVAILABLE.label,
        )
        UNKNOWN = AvailabilitiesBase.UNKNOWN.value, AvailabilitiesBase.UNKNOWN.label

    name = models.CharField(_("Name"), max_length=20)
    description = models.TextField(_("Description"))
    availability = models.CharField(
        _("Availability"),
        max_length=11,
        choices=Availabilities.choices,
        default=Availabilities.UNKNOWN,
    )


class EventQuerySet(models.QuerySet):
    def overlaped_to(
        self,
        start: datetime,
        end: datetime = None,
        intersection=False,
        recuring=False,
        all_day=False,
    ):
        """Filters events that are overlaped to given period.

        Args:
            start (datetime): Start of period.
            end (datetime, optional): End of period. Defaults to None and then filtered will be only start.
            intersection (bool, optional): If true events that have equal start_date to <end> or end_date to <start> will be also counted. Defaults to False.
            recuring (bool, optional): _description_. Defaults to False.
            all_day (bool, optional): _description_. Defaults to False.

        Raises:
            NotImplementedError: _description_

        Returns:
            _type_: _description_
        """
        if recuring or all_day:
            raise NotImplementedError()

        # run for single parameter
        if not end:
            if intersection:
                return self.filter(Q(start_date__lte=start) & Q(end_date__gte=start))
            return self.filter(Q(start_date__lt=start) & Q(end_date__gt=start))

        if intersection:
            return self.filter(
                Q(start_date__lte=start) & Q(end_date__gte=start)  # 1
                | Q(start_date__lte=end) & Q(end_date__gte=end)  # 2
                | Q(start_date=start)  # 3
                | Q(start_date__gte=start) & Q(end_date__lte=end)  # 4
            )

        """Scenearios:
        SD - start_date, ED - end_date, S - start, E - end
        #(1|2) S------E
        #(1|2)         S----------E
        #(1|2)        S---E
        #3         S-----------E
        #3         S-----E | ------E
        #4     S------------------E
        #4    S----------------E
                   SD---------ED
        """
        return self.filter(
            Q(start_date__lt=start) & Q(end_date__gt=start)  # 1
            | Q(start_date__lt=end) & Q(end_date__gt=end)  # 2
            | Q(start_date=start)  # 3
            | Q(start_date__gt=start) & Q(end_date__lte=end)  # 4
        )


class Event(UUIDModel, TimestampsModel):
    class Availabilities(models.TextChoices):
        BUSY = AvailabilitiesBase.BUSY.value, AvailabilitiesBase.BUSY.label
        UNAVAILABLE = (
            AvailabilitiesBase.UNAVAILABLE.value,
            AvailabilitiesBase.UNAVAILABLE.label,
        )
        UNKNOWN = AvailabilitiesBase.UNKNOWN.value, AvailabilitiesBase.UNKNOWN.label

    name = models.CharField(_("Name"), max_length=20)
    description = models.TextField(_("Description"))

    start_date = models.TimeField()
    end_date = models.TimeField(
        null=True
    )  # only when availability is BUSY - couse user start practice and don't know when he will finish
    is_all_day = models.BooleanField(default=False)
    duration = models.IntegerField(default=0)
    is_recuring = models.BooleanField(default=False, editable=False)
    recurence = RecurrenceField()

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    availability = models.CharField(
        _("Availability"),
        max_length=11,
        choices=Availabilities.choices,
        default=Availabilities.UNKNOWN,
    )

    objects = EventQuerySet.as_manager()


class Report(UUIDModel, TimestampsModel):
    class Availabilities(models.TextChoices):
        FREE = AvailabilitiesBase.FREE.value, AvailabilitiesBase.FREE.label
        BUSY = AvailabilitiesBase.BUSY.value, AvailabilitiesBase.BUSY.label

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    availability = models.CharField(
        max_length=11,
        choices=Availabilities.choices,
    )
