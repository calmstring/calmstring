from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from recurrence.fields import RecurrenceField
import recurrence

from utils.models import UUIDModel, TimestampsModel, SoftDeleteModel, SoftDeleteQuerySet

from datetime import datetime, timedelta, time, date
from . import signals as events_signals
from utils.dates import tz_datetime

# Create your models here.


class AvailabilitiesBase(models.TextChoices):
    BUSY = "BUSY", _("Busy")
    FREE = "FREE", _("Free")
    UNAVAILABLE = "UNAVAILABLE", _("Unavailable")
    UNKNOWN = "UNKNOWN", _("Unknown")


class EventRoom(UUIDModel):  # change to room calendar
    class Availabilities(models.TextChoices):
        BUSY = AvailabilitiesBase.BUSY.value, AvailabilitiesBase.BUSY.label
        FREE = AvailabilitiesBase.FREE.value, AvailabilitiesBase.FREE.label
        UNAVAILABLE = (
            AvailabilitiesBase.UNAVAILABLE.value,
            AvailabilitiesBase.UNAVAILABLE.label,
        )
        UNKNOWN = AvailabilitiesBase.UNKNOWN.value, AvailabilitiesBase.UNKNOWN.label

    availability = models.CharField(
        _("Availability"),
        max_length=11,
        choices=Availabilities.choices,
        default=Availabilities.UNKNOWN,
    )

    room = models.ForeignKey(
        settings.ROOM_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Room"),
    )

    def __str__(self):
        return f"{self.room.name} - {self.availability}"


class EventQuerySet(SoftDeleteQuerySet):
    def overlaped_to(
        self,
        start: datetime,
        end: datetime = None,
        intersection=False,
        all_day=False,
    ):
        """Filters events that are overlaped to given period.

        WARNING!
        This method in case of recurrent events relies on weekly_occurences,
        so to get correct result for recurrent events, you need to call set_occurrences(),
        for your events.


        Args:
            start (datetime): Start of period.
            end (datetime, optional): End of period. Defaults to None and then filtered will be only start.
            intersection (bool, optional): If true events that have equal start_date to <end> or end_date to <start> will be also counted. Defaults to False.
            recurring (bool, optional): _description_. Defaults to False.
            all_day (bool, optional): _description_. Defaults to False.

        Raises:
            NotImplementedError: _description_

        Returns:
            _type_: _description_
        """
        not_recurring = self.none()
        recurring = self.none()

        start_time = start.time()
        start_date = start.date()

        # run for single parameter
        if not end:
            if intersection:
                not_recurrring = self.filter(
                    Q(is_recurring=False),
                    Q(start_date__lte=start) & Q(end_date__gte=start),
                )

                recurring = self.filter(
                    Q(is_recurring=True),
                    Q(occurrences__has_key=str(start_date)),
                    Q(start_date__time__lte=start_time)
                    & Q(end_date__time__gte=start_time),
                )
            else:
                not_recurrring = self.filter(
                    Q(start_date__lt=start) & Q(end_date__gt=start)
                )
                recurring = self.filter(
                    Q(is_recurring=True),
                    Q(occurrences__has_key=str(start_date)),
                    Q(start_date__time__lt=start_time)
                    & Q(end_date__time__gt=start_time),
                )
            return not_recurrring | recurring

        end_time = end.time()

        if intersection:
            not_recurring = self.filter(
                Q(is_recurring=False),
                Q(start_date__lte=start) & Q(end_date__gte=start)  # 1
                | Q(start_date__lte=end) & Q(end_date__gte=end)  # 2
                | Q(start_date=start)  # 3
                | Q(start_date__gte=start) & Q(end_date__lte=end),  # 4
            )

            # it's same as above, but for recurrent events
            recurring = self.filter(
                Q(is_recurring=True),
                Q(occurrences__has_key=str(start_date)),
                Q(start_date__time__lte=start_time)
                & Q(end_date__time__gte=start_time)  # 1
                | Q(start_date__time__lte=end_time)
                & Q(end_date__time__gte=end_time)  # 2
                | Q(start_date__time=start_time)  # 3
                | Q(start_date__time__gte=start_time)
                & Q(end_date__time__lte=end_time),  # 4
            )

        else:
            not_recurring = self.filter(
                Q(is_recurring=False),
                Q(start_date__lt=start) & Q(end_date__gt=start)  # 1
                | Q(start_date__lt=end) & Q(end_date__gt=end)  # 2
                | Q(start_date=start)  # 3
                | Q(start_date__gt=start) & Q(end_date__lte=end),  # 4
            )

            recurring = self.filter(
                Q(is_recurring=True),
                Q(occurrences__has_key=str(start_date)),
                Q(start_date__time__lt=start_time)
                & Q(end_date__time__gt=start_time)  # 1
                | Q(start_date__time__lt=end_time) & Q(end_date__time__gt=end_time)  # 2
                | Q(start_date__time=start_time)  # 3
                | Q(start_date__time__gt=start_time)
                & Q(end_date__time__lte=end_time),  # 4
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

        return not_recurring | recurring


class Event(UUIDModel, TimestampsModel, SoftDeleteModel):
    class Availabilities(models.TextChoices):
        BUSY = AvailabilitiesBase.BUSY.value, AvailabilitiesBase.BUSY.label
        UNAVAILABLE = (
            AvailabilitiesBase.UNAVAILABLE.value,
            AvailabilitiesBase.UNAVAILABLE.label,
        )
        UNKNOWN = AvailabilitiesBase.UNKNOWN.value, AvailabilitiesBase.UNKNOWN.label

    name = models.CharField(_("Name"), max_length=70, blank=True, null=True, default="")
    description = models.TextField(_("Description"), null=True, blank=True, default="")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(
        null=True
    )  # only when availability is BUSY - couse user start practice and don't know when he will finish
    is_all_day = models.BooleanField(default=False)
    duration = models.IntegerField(default=0)
    is_recurring = models.BooleanField(default=False, editable=False)
    recurrences = RecurrenceField(null=True, include_dtstart=False)
    next_occurrence = models.DateField(null=True, default=None)

    room = models.ForeignKey(EventRoom, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    occurrences = models.JSONField(default=dict)

    availability = models.CharField(
        _("Availability"),
        max_length=11,
        choices=Availabilities.choices,
        default=Availabilities.UNKNOWN,
    )

    objects = EventQuerySet.as_manager()

    def get_next_occurrence(self, date_from=None):
        if not self.is_recurring:
            return None

        today = date_from or timezone.now().date()

        today_datetime = datetime.combine(today, time.min)

        _next_occurrence = self.recurrences.after(
            today_datetime,
            inc=True,
            dtstart=timezone.make_naive(self.start_date),
        )
        if _next_occurrence:
            _next_occurrence = _next_occurrence.date()
        return _next_occurrence

    def get_occurrences(self, date_from, date_to, dtstart: datetime = None):
        # You need to be very careful with this method.
        # Check if start_date and end_date are valid in relation to recurrences

        if not self.is_recurring:
            return []

        date_start = dtstart or self.start_date

        if not timezone.is_naive(date_start):
            date_start = timezone.make_naive(date_start)

        return self.recurrences.between(
            date_from - timedelta(days=1),
            date_to + timedelta(days=1),
            dtstart=date_start,
        )

    def set_next_occurrence(self, date_from=None):

        _next_occurrence = self.get_next_occurrence(date_from)

        self.next_occurrence = _next_occurrence

        self.save()

        events_signals.event_set_next_occurrence.send(sender=self.__class__, event=self)

        return _next_occurrence

    # temporary use naive datetime
    @property
    def recurrences_until(self):
        for rrule in self.recurrences.rrules:
            if rrule.until:
                if not timezone.is_naive(rrule.until):
                    return timezone.make_naive(rrule.until)
                return rrule.until
        return datetime.max

    @classmethod
    def prepare_occurrences_for_db(cls, occurrences_list):
        """Used when we want to save occurrences to db.
        This methods converts list: [datetime.datetime, datetime.datetime] to {'yyyy-mm-dd':True,...}
        """
        return {dt: True for dt in map(lambda dt: str(dt.date()), occurrences_list)}

    def prepare_occurrences_from_db(self):
        """This method converts occurrences to date list"""
        occurrences = self.occurrences.keys()

        occurrences = sorted(map(lambda dt: date.fromisoformat(dt), occurrences))

        return occurrences


class Report(UUIDModel, TimestampsModel):
    class Availabilities(models.TextChoices):
        BUSY = AvailabilitiesBase.BUSY.value, AvailabilitiesBase.BUSY.label
        FREE = AvailabilitiesBase.FREE.value, AvailabilitiesBase.FREE.label
        UNAVAILABLE = (
            AvailabilitiesBase.UNAVAILABLE.value,
            AvailabilitiesBase.UNAVAILABLE.label,
        )

    date = models.DateTimeField()
    name = models.CharField(_("Name"), max_length=70)
    description = models.TextField(_("Description"), null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    reported_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="report_reported_users",
        blank=True,
        default=None,
    )

    room = models.ForeignKey(EventRoom, on_delete=models.CASCADE)
    availability = models.CharField(
        max_length=11,
        choices=Availabilities.choices,
    )
