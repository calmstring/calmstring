from .models import Room, Event, Report
from . import exceptions


def occupy_room(room, user, start_date, end_date):
    """
    Rules:
    - can't accupy room for whole day
    - can't occupy room as recurently
    - can't occupy when there is already occupied room
    - can't occupy room for another user
    """
    if end_date:
        if start_date == end_date or start_date > end_date:
            raise exceptions.ValidationError()

    user_events = Event.objects.filter(
        author=user, availability=Event.Availabilities.BUSY
    )

    # Can't occupy room if user has event not ended
    if user_events.filter(end_date=None).exists():
        raise exceptions.NotEndedEventExists()

    # Can't occupy room if user has event overlaped with new event
    if user_events.overlaped_to(start_date, end_date).exists():
        raise exceptions.OverlapedEventExists()

    return Event.objects.create(
        author=user,
        room=room,
        start_date=start_date,
        end_date=end_date,
        availability=Event.Availabilities.BUSY,
    )


def free_room(room, user, data):
    pass


def report_unavailable(room, user, data):
    pass


def report_free(room, user, data):
    pass


def report_busy(room, user, occupied_by, data):
    pass
