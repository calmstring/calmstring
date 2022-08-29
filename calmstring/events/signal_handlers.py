from django.dispatch import receiver
from django.utils import timezone
import changes.signals
import rooms.signals
from . import signals as events_signals
from . import tasks, conf, logic


@receiver(
    [
        events_signals.report_unavailable_created,
        events_signals.report_unavailable_edited,
    ]
)
def event_occurrences_handler(sender, **kwargs):
    if "report" in kwargs.keys():
        return

    event = kwargs["event"]

    tasks.call_set_event_occurrences(
        event.id,
    )


def basic_room_availability_handler(event):
    if event.start_date > timezone.now():
        tasks.call_set_event_room_availability.schedule(
            (event.room.id), eta=event.start_date
        )
    else:
        tasks.call_set_event_room_availability(event.room.id)

    if event.end_date:
        tasks.call_set_event_room_availability.schedule(
            (event.room.id,), eta=event.end_date
        )


@receiver(
    [
        events_signals.occupy_created,
        events_signals.occupy_edited,
        events_signals.occupy_ended,
    ]
)
def room_availability_handler_for_busy(sender, **kwargs):
    event = kwargs["event"]

    basic_room_availability_handler(event)


@receiver(
    [
        events_signals.report_unavailable_created,
        events_signals.report_unavailable_edited,
    ]
)
def room_availability_handler_for_unavailable_not_recurring(sender, **kwargs):
    if "report" in kwargs:
        return

    event = kwargs["event"]

    if event.is_recurring:
        return

    basic_room_availability_handler(event)


@receiver([events_signals.event_set_occurrences])
def room_availability_handler_for_recurring_events(sender, **kwargs):
    event = kwargs["event"]
    occurrences = kwargs["occurrences"]

    if not len(occurrences):
        return

    first_occurence_date_iso = occurrences[0].date().isoformat()

    tasks.schedule_for_recurrent_event_call_set_event_room_availability(
        event.id, first_occurence_date_iso
    )


"""External events"""


@receiver(changes.signals.change_reverted)
def event_change_reverted_handler(sender, reverted, to, content_object, **kwargs):
    from .models import Event, Report

    if not isinstance(content_object, Event) and not isinstance(content_object, Report):
        return None

    CHANGE_TYPES = conf.CHANGE_TYPES

    change_type = to.type
    author = to.author

    signal_kwargs = {"sender": "event_change_reverted_handler", "event": content_object}

    # restore is called in case content_object was deleted
    # but also calls save() method and this is what we want
    if change_type in [
        CHANGE_TYPES.OCCUPY_ROOM_CREATED,
        CHANGE_TYPES.OCCUPY_ROOM_EDITED,
    ]:
        content_object.restore(save=False)
        logic.edit_occupy_room(
            content_object, author, emit_external_signals=False, force_edit=True
        )
    elif change_type == CHANGE_TYPES.OCCUPY_ROOM_DELETED:
        logic.delete_occupy_room(content_object, author, emit_external_signals=False)
    elif change_type == [
        CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_EVENT_CREATED,
        CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_EVENT_EDITED,
    ]:
        content_object.restore(save=False)
        logic.edit_report_unavailable_event(
            content_object, author, emit_external_signals=False, force_edit=True
        )

    elif change_type == CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_EVENT_DELETED:
        logic.delete_report_unavailable_event(
            content_object, author, emit_external_signals=False
        )
    elif change_type == [
        CHANGE_TYPES.REPORT_ROOM_UNAVAILABLE_CREATED,
        CHANGE_TYPES.REPORT_ROOM_FREE_CREATED,
    ]:
        content_object.restore()
        # not other action to do
    else:
        pass


@receiver(rooms.signals.room_created)
def create_event_room_handler(sender, room, **kwargs):
    from .models import EventRoom

    EventRoom.objects.create(room=room)
