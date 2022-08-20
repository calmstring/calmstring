from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from .models import Event, Report, EventRoom


from . import exceptions, conf
import changes.signals
from . import signals as events_signals


import recurrence

from datetime import datetime, timedelta
from utils.dates import is_all_day
from utils.logic import signals_emiter

import logging

logger = logging.getLogger(__name__)


def occupy_room(
    room: EventRoom,
    user,
    start_date: datetime,
    end_date: datetime = None,
    name: str = "",
    description: str = "",
    **kwargs,
):
    """User want to occupy room
    Rules:
    - can't accupy room for whole day
    - can't occupy room as recurently
    - can't occupy when there is already occupied room
    - can't occupy room for another user

    Args:
        room (EventRoom): _description_
        user (User): _description_
        start_date (datetime): _description_
        end_date (datetime, optional): _description_. Defaults to None.
        name (str, optional): _description_. Defaults to "".
        description (str, optional): _description_. Defaults to "".
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Raises:
        exceptions.NotEndedEventExists: _description_
        exceptions.OverlapedEventExists: _description_

    Returns:
        (event): Created event
    """

    user_events = Event.objects.existing().filter(
        Q(author=user),
        Q(availability=Event.Availabilities.BUSY)
        | Q(availability=Event.Availabilities.UNAVAILABLE),
    )

    # Can't occupy room if user has event not ended
    if user_events.filter(end_date=None).exists():
        raise exceptions.NotEndedEventExists()

    # Can't occupy room if user has event overlaped with new event
    if user_events.overlaped_to(start_date, end_date).exists():
        raise exceptions.OverlapedEventExists()

    event = Event.objects.create(
        author=user,
        room=room,
        start_date=start_date,
        end_date=end_date,
        availability=Event.Availabilities.BUSY,
        name=name,
        description=description,
    )

    def internal_signals():
        events_signals.occupy_created.send_robust(
            sender="occupy_room",
            event=event,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="occupy_room",
            author=user,
            content_object=event,
            type=conf.CHANGE_TYPES.OCCUPY_ROOM_CREATED,
            name=conf.MESSAGES.OCCUPY_ROOM(room, user),
            uuid=room.uuid,
        )

    signals_emiter(internal_signals, external_signals, **kwargs)

    return event


def free_room(room: EventRoom, user, end_date: datetime, **kwargs):
    """User want to free room when he didn't done when he was occupying it

    Args:
        user (User): User who want to free room
        end_date (datetime): Date when user want to free room
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Raises:
        exceptions.MultipleNotEndedEventsExists: When user has multiple not ended events
        exceptions.NotEndedEventDoesNotExist: When user has no not ended events
        exceptions.ValidationError: When end_date is before start_date
        exceptions.ValidationError: When occuping duration is to long

    Returns:
        (Event): Event that user freed room
    """
    user_not_ended_events = Event.objects.existing().filter(
        author=user, availability=Event.Availabilities.BUSY, end_date=None
    )

    if len(user_not_ended_events) > 1:
        logger.error(f"Multiple not ended events exists, Author: {user.uuid}")
        raise exceptions.MultipleNotEndedEventsExists()
    elif not len(user_not_ended_events):
        raise exceptions.NotEndedEventDoesNotExist()

    user_event = user_not_ended_events.first()

    if user_event.room != room:
        logger.error(
            f"Wrong room provided, Author: {user.uuid}, provided: {user_event.room}, should be: {room.uuid}"
        )
        raise exceptions.WrongRoomProvided()

    user_event.end_date = end_date
    user_event.save()

    def internal_signals():
        events_signals.occupy_ended.send_robust(
            sender="free_room",
            event=user_event,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="free_room",
            author=user,
            content_object=user_event,
            type=conf.CHANGE_TYPES.OCCUPY_ROOM_EDITED,
            name=conf.MESSAGES.FREE_ROOM(user_event, user),
            uuid=user_event.room.uuid,
        )

    signals_emiter(
        internal_signals,
        external_signals,
        **kwargs,
    )

    return user_event


def report_unavailable(
    room: EventRoom,
    user,
    start_date: datetime,
    end_date: datetime = None,
    name: str = None,
    description: str = None,
    recurrences: recurrence.Recurrence = None,
    **kwargs,
):
    """Report that room is unavailable creates report object or event, depending on end_date

    Args:
        room (EventRoom): _description_
        user (User): _description_
        start_date (datetime): _description_
        end_date (datetime, optional): _description_. Defaults to None.
        name (str, optional): _description_. Defaults to None.
        description (str, optional): _description_. Defaults to None.
        recurrences (recurrence.Recurrence, optional): _description_. Defaults to None.
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Returns:
        (Report or Event): created report or event object
    """

    get_name = lambda: name or _("Unavailable")

    if not end_date:
        report = Report.objects.create(
            date=start_date,
            availability=Report.Availabilities.UNAVAILABLE,
            room=room,
            author=user,
            name=get_name(),
            description=description,
        )

        def internal_signals():
            events_signals.report_unavailable_created.send_robust(
                sender="report_unavailable",
                report=report,
            )

        def external_signals():
            changes.signals.change_done.send_robust(
                sender="report_unavailable",
                author=user,
                content_object=event,
                type=conf.CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_CREATED,
                name=conf.MESSAGES.REPORT_UNAVAILABLE(report, user),
                uuid=room.uuid,
            )

        signals_emiter(internal_signals, external_signals, **kwargs)

        return report

    _is_all_day, tdelta = is_all_day(start_date, end_date)

    event = Event.objects.create(
        room=room,
        author=user,
        start_date=start_date,
        end_date=end_date,
        name=get_name(),
        description=description,
        recurrences=recurrences,
        is_recurring=bool(recurrences),
        is_all_day=_is_all_day,
        duration=int(tdelta.total_seconds()),
        availability=Event.Availabilities.UNAVAILABLE,
    )

    def internal_signals():
        events_signals.report_unavailable_created.send_robust(
            sender="report_unavailable",
            event=event,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="report_unavailable",
            author=user,
            content_object=event,
            type=conf.CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_EVENT_CREATED,
            name=conf.MESSAGES.REPORT_UNAVAILABLE_EVENT(event, user),
            uuid=room.uuid,
        )

    signals_emiter(internal_signals, external_signals, **kwargs)

    return event


def report_free(
    room: EventRoom,
    user,
    date: datetime,
    name: str = None,
    description: str = None,
    **kwargs,
):
    """Report taht room is free creates report object

    Args:
        room (EventRoom): _description_
        user (User): _description_
        date (datetime): _description_
        name (str, optional): _description_. Defaults to None.
        description (str, optional): _description_. Defaults to None.
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Returns:
        Report: created report object
    """

    get_name = lambda: name or Report.Availabilities.FREE.label

    report = Report.objects.create(
        date=date,
        name=get_name(),
        description=description,
        author=user,
        room=room,
        availability=Report.Availabilities.FREE,
    )

    def internal_signals():
        events_signals.report_free_created.send_robust(
            sender="report_free",
            report=report,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="report_free",
            author=user,
            content_object=report,
            type=conf.CHANGE_TYPES.REPORT_ROOM_FREE_CREATED,
            name=conf.MESSAGES.REPORT_FREE(report, user),
            uuid=room.uuid,
        )

    signals_emiter(internal_signals, external_signals, **kwargs)
    return report


def report_busy(
    room: EventRoom,
    user,
    date: datetime,
    reported_users: list = None,
    name: str = None,
    description: str = None,
    **kwargs,
):
    """Report taht room is busy creates report object

    Args:
        room (EventRoom): _description_
        user (User): _description_
        date (datetime): _description_
        reported_users (list, optional): _description_. Defaults to None.
        name (str, optional): _description_. Defaults to None.
        description (str, optional): _description_. Defaults to None.
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Returns:
        Report: created report object
    """

    get_name = lambda: name or Report.Availabilities.BUSY.label

    report = Report.objects.create(
        date=date,
        name=get_name(),
        description=description,
        author=user,
        room=room,
        availability=Report.Availabilities.FREE,
    )
    if reported_users:
        report.reported_users.set(reported_users)

    def internal_signals():
        events_signals.report_busy_created.send_robust(
            sender="report_busy",
            report=report,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="report_busy",
            author=user,
            content_object=report,
            type=conf.CHANGE_TYPES.REPORT_ROOM_BUSY_CREATED,
            name=conf.MESSAGES.REPORT_BUSY(report, user),
            uuid=room.uuid,
        )

    signals_emiter(internal_signals, external_signals, **kwargs)

    return report


def _edit_event(event, **kwargs):
    start_date_or_end_date_in_kwargs = False
    change = False
    start_date = event.start_date
    if "start_date" in kwargs.keys():
        start_date = kwargs["start_date"]
        start_date_or_end_date_in_kwargs = True

    end_date = event.end_date
    if "end_date" in kwargs.keys():
        end_date = kwargs["end_date"]
        start_date_or_end_date_in_kwargs = True

    if start_date_or_end_date_in_kwargs:
        event.duration = int(abs(end_date - start_date).total_seconds())

        event.start_date = start_date
        event.end_date = end_date

    change = start_date_or_end_date_in_kwargs

    if "name" in kwargs.keys():
        event.name = kwargs["name"]
        change = True

    if "description" in kwargs.keys():
        event.description = kwargs["description"]
        change = True

    return change


def edit_occupy_room(
    event: Event,
    user,
    emit_signals: bool = True,
    emit_internal_signals: bool = True,
    emit_external_signals: bool = True,
    force_edit: bool = False,
    **kwargs,
):
    """Edit occupy room event

    Args:
        event (Event): _description_
        **kwargs: start_date, end_date, name, description
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.
        force_edit (bool, optional): Saves object even if not changes provided (usefull when we wanna to pass already changed object). Defaults to False.

    Raises:
        exceptions.ValidationError: When event availability is not OCCUPY
        exceptions.OverlapedEventExists: When overlaped event exists

    Returns:
        _type_: _description_
    """
    if event.availability != Event.Availabilities.BUSY:
        raise exceptions.ValidationError(_("Event is not busy"))

    change = _edit_event(event, **kwargs)

    if not change and not force_edit:
        return event

    user_events = (
        Event.objects.existing()
        .filter(
            Q(author=user),
            Q(availability=Event.Availabilities.BUSY)
            | Q(availability=Event.Availabilities.UNAVAILABLE),
        )
        .exclude(id=event.id)
    )
    start_date = event.start_date
    end_date = event.end_date
    # Can't occupy room if user has event overlaped with new event
    if user_events.overlaped_to(start_date, end_date).exists():
        raise exceptions.OverlapedEventExists()

    event.save()

    def internal_signals():
        events_signals.occupy_edited.send_robust(
            sender="edit_occupy_room",
            event=event,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="edit_occupy_room",
            author=user,
            content_object=event,
            type=conf.CHANGE_TYPES.OCCUPY_ROOM_EDITED,
            name=conf.MESSAGES.OCCUPY_EDITED(event, user),
            uuid=event.room.uuid,
        )

    signals_emiter(
        internal_signals,
        external_signals,
        emit_signals=emit_signals,
        emit_internal_signals=emit_internal_signals,
        emit_external_signals=emit_external_signals,
    )

    return event


def delete_occupy_room(event: Event, user, **kwargs):
    """Delete occupy room event (soft delete)

    Args:
        event (Event): _description_
        user (_type_): _description_
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Returns:
        Event: soft deleted event
    """
    if event.availability != Event.Availabilities.BUSY:
        raise exceptions.ValidationError(_("Event is not busy"))

    event.soft_delete()

    def internal_signals():
        events_signals.occupy_deleted.send_robust(
            sender="delete_occupy_room", event=event
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="delete_occupy_room",
            author=user,
            content_object=event,
            type=conf.CHANGE_TYPES.OCCUPY_ROOM_DELETED,
            name=conf.MESSAGES.OCCUPY_DELETE(event, user),
            uuid=event.room.uuid,
        )

    signals_emiter(internal_signals, external_signals, **kwargs)

    return event


def edit_report_unavailable_event(
    event: Event,
    user,
    emit_signals: bool = True,
    emit_internal_signals: bool = True,
    emit_external_signals: bool = True,
    force_edit: bool = False,
    **kwargs,
):
    """Edit report unavailable event

    Args:
        event (Event): _description_
        user (_type_): _description_
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.
        force_edit (bool, optional): Saves object even if not changes provided (usefull when we wanna to pass already changed object). Defaults to False.
        **kwargs: start_date, end_date, name, description

    Raises:
        exceptions.ValidationError: _description_

    Returns:
        event: Edited unavailable event
    """
    if event.availability != Event.Availabilities.UNAVAILABLE:
        raise exceptions.ValidationError(_("Event is not unavailable"))

    change = _edit_event(event, **kwargs)

    if "recurrences" in kwargs.keys():
        change = True
        if not kwargs["recurrences"]:
            event.recurrences = None
            event.is_recurring = False
            event.occurrences = {}
        else:
            event.recurrences = kwargs["recurrences"]
            event.is_recurring = True

    if not change and not force_edit:
        return event
    event.save()

    def internal_signals():
        events_signals.report_unavailable_edited.send_robust(
            sender="edit_report_unavailable_event",
            event=event,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="edit_report_unavailable_event",
            author=user,
            content_object=event,
            type=conf.CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_EVENT_EDITED,
            name=conf.MESSAGES.REPORT_UNAVAILABLE_EVENT_EDITED(event, user),
            uuid=event.room.uuid,
        )

    signals_emiter(
        internal_signals,
        external_signals,
        emit_signals=emit_signals,
        emit_internal_signals=emit_internal_signals,
        emit_external_signals=emit_external_signals,
    )
    return event


def delete_report_unavailable_event(event: Event, user, **kwargs):
    """_summary_

    Args:
        event (Event): _description_
        user (_type_): _description_
        emit_signals (bool, optional): _description_. Defaults to True.
        emit_internal_signals (bool, optional): _description_. Defaults to True.
        emit_external_signals (bool, optional): _description_. Defaults to True.

    Raises:
        exceptions.ValidationError: _description_

    Returns:
        _type_: _description_
    """

    if event.availability != Event.Availabilities.UNAVAILABLE:
        raise exceptions.ValidationError(_("Event is not unavailable"))

    event.soft_delete()

    def internal_signals():
        events_signals.report_unavailable_deleted.send_robust(
            sender="delete_report_unavailable_event",
            event=event,
        )

    def external_signals():
        changes.signals.change_done.send_robust(
            sender="delete_report_unavailable_event",
            author=user,
            content_object=event,
            type=conf.CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_EVENT_DELETED,
            name=conf.MESSAGES.REPORT_UNAVAILABLE_EVENT_DELETED(event, user),
            uuid=event.room.uuid,
        )

    signals_emiter(internal_signals, external_signals, **kwargs)

    return event


def set_event_occurrences(
    event: Event, dtstart: datetime = None, period=None, **kwargs
):
    """Set occurrences for event for period from dtstart

    Args:
        event (Event): _description_
        dtstart (datetime, optional): Date start of the period. Defaults to None.
        period (_type_, optional): The period for which the events will be set (from dtstart) - in seconds. Defaults to conf.OCCURRENCES_PERIOD.

    Returns:
        (datetime (timezone)|None): datetime of the end of the period if next occurrences are found
    """

    _period = period or conf.OCCURRENCES_PERIOD

    if not event.is_recurring:
        return None

    period_timedelta = timedelta(seconds=_period)

    # Get occurrences for given period from dtstart
    period_start_date = dtstart or timezone.now()
    if not timezone.is_naive(period_start_date):
        period_start_date = timezone.make_naive(period_start_date)

    period_end_date = period_start_date + period_timedelta
    occurrences = event.get_occurrences(
        period_start_date,
        period_end_date,
        dtstart=timezone.make_naive(event.start_date),
    )

    # Check if occurrences exist and get next_schedule date
    # to call from external worker set_event_occurrences again later
    if not len(occurrences):
        return None

    event.occurrences = Event.prepare_occurrences_for_db(occurrences)
    event.save()

    def internal_signals():
        events_signals.event_set_occurrences.send_robust(
            sender="set_event_occurrences", event=event, occurrences=occurrences
        )

    def external_signals():
        pass

    signals_emiter(internal_signals, external_signals, **kwargs)

    if event.recurrences_until < period_start_date:
        return None

    next_schedule = timezone.make_aware(
        datetime.combine(period_end_date.date(), event.start_date.time())
    )
    return next_schedule


def get_event_room_availability(room: EventRoom, datetime_at: datetime = None):
    """Get room availability status at given datetime_at"""

    # use just existing events
    pending_events = (
        Event.objects.filter(room=room)
        .existing()
        .overlaped_to(datetime_at, intersection=True)
    )

    if not len(pending_events):
        return EventRoom.Availabilities.FREE

    # To make sure if event ends e.g. on 12:00,
    # then room availability in makred as free from 12:00
    latests_ended = pending_events.order_by("-end_date__time").first()
    if latests_ended.end_date.time() == datetime_at.time():
        return EventRoom.Availabilities.FREE

    statuses_set = set(map(lambda event: event.availability, pending_events))
    if len(statuses_set) > 1:
        return EventRoom.Availabilities.UNKNOWN

    if statuses_set == {Event.Availabilities.UNAVAILABLE}:
        return EventRoom.Availabilities.UNAVAILABLE

    if statuses_set == {Event.Availabilities.BUSY}:
        return EventRoom.Availabilities.BUSY

    return EventRoom.Availabilities.UNKNOWN


def set_event_room_availability(room, **kwargs):
    availability = get_event_room_availability(room, timezone.now())
    room.availability = availability
    room.save()

    def internal_signals():
        events_signals.room_availability_changed.send_robust(
            sender="set_event_room_availability",
            room=room,
        )

        if room.availability == room.Availabilities.BUSY:
            events_signals.room_availability_busy.send_robust(
                sender="set_event_room_availability", room=room
            )
        elif room.availability == room.Availabilities.FREE:
            events_signals.room_availability_free.send_robust(
                sender="set_event_room_availability", room=room
            )
        elif room.availability == room.Availabilities.UNAVAILABLE:
            events_signals.room_availability_unavailable.send_robust(
                sender="set_event_room_availability", room=room
            )
        else:
            events_signals.room_availability_unknown.send_robust(
                sender="set_event_room_availability", room=room
            )

    def external_signals():
        pass

    signals_emiter(internal_signals, external_signals, **kwargs)
