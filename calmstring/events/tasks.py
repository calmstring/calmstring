from datetime import datetime, timedelta, date
from multiprocessing.sharedctypes import Value
from django.utils import timezone
from huey.contrib.djhuey import db_task

from .models import Event, EventRoom
from . import logic


@db_task()
def set_event_next_occurrence(event_id):
    event = Event.objects.get(id=event_id)
    event.set_next_occurrence()


@db_task()
def call_set_event_occurrences(event_id):
    event = Event.objects.get(id=event_id)
    next_schedule = logic.set_event_occurrences(event)

    if next_schedule:
        call_set_event_occurrences.schedule((event_id,), eta=next_schedule)


@db_task()
def call_set_event_room_availability(room_event_id):
    event_room = EventRoom.objects.get(id=room_event_id)

    logic.set_event_room_availability(event_room)


@db_task()
def schedule_for_recurrent_event_call_set_event_room_availability(event_id, occurrence_date):
    event = Event.objects.get(id=event_id)

    occurrences = event.prepare_occurrences_from_db()

    current_occurrence = date.fromisoformat(occurrence_date)

    next_schedule_start = timezone.make_aware(
        datetime.combine(current_occurrence, event.start_date.time())
    )

    next_schedule_end = next_schedule_start + timedelta(seconds=event.duration)

    call_set_event_room_availability.schedule((event.room.id,), eta=next_schedule_start)
    call_set_event_room_availability.schedule((event.room.id,), eta=next_schedule_end)

    current_date_index = occurrences.index(current_occurrence)
    try:
        next_date = occurrences[current_date_index + 1]
    except IndexError:
        return

    schedule_for_recurrent_event_call_set_event_room_availability.schedule(
        (event.room.id, next_date.isoformat()), eta=next_schedule_end
    )
