from django.conf import settings as dj_settings
from django.utils.translation import gettext_lazy as _
import sys


class Conf:
    def _setting(self, name, default):
        conf = getattr(dj_settings, "CALMSTRING", {})
        return conf.get(name, default)

    @property
    def MAX_BUSY_DURATION(self):
        return self._setting("MAX_BUSY_DURATION", 60 * 60 * 16)

    @property
    def GAP_BETWEEN_EVENTS(self):
        return self._setting("GAP_BETWEEN_EVENTS", 60 * 5)

    @property
    def OCCURRENCES_PERIOD(self):
        value = self._setting("OCCURRENCES_PERIOD", 60 * 60 * 24 * 7)
        assert value >= (60 * 60 * 24 * 2)  # two days
        return value

    @classmethod
    def get_room(cls, event_room):
        return event_room.room

    class CHANGE_TYPES:
        OCCUPY_ROOM_CREATED = "OCCUPY_ROOM_CREATED"
        OCCUPY_ROOM_EDITED = "OCCUPY_ROOM_EDITED"
        OCCUPY_ROOM_DELETED = "OCCUPY_ROOM_DELETED"
        REPORT_ROOM_UNAVAILABLE_EVENT_CREATED = "REPORT_ROOM_UNAVAILABLE_EVENT_CREATED"
        REPORT_ROOM_UNAVAILABLE_EVENT_EDITED = "REPORT_ROOM_UNAVAILABLE_EVENT_EDITED"
        REPORT_ROOM_UNAVAILABLE_EVENT_DELETED = "REPORT_ROOM_UNAVAILABLE_EVENT_DELETED"
        REPORT_ROOM_UNAVAILABLE_CREATED = "REPORT_ROOM_UNAVAILABLE_CREATED"

        REPORT_ROOM_FREE_CREATED = "REPORT_ROOM_FREE_CREATED"
        REPORT_ROOM_BUSY_CREATED = "REPORT_ROOM_BUSY_CREATED"

    class MESSAGES:
        OCCUPY_ROOM = lambda room, user: _('{user} created busy room "{room}"').format(
            user=user.username, room=Conf.get_room(room).name
        )

        FREE_ROOM = lambda event, user: _(
            '{user} released room "{room_name}" at {released_at}'
        ).format(
            user=user.username,
            room_name=Conf.get_room(event.room).name,
            released_at=event.end_date,
        )

        REPORT_UNAVAILABLE_EVENT = lambda event, user: _(
            '{user} reported unavailable room "{room_name}"'
        ).format(user=user.username, room_name=Conf.get_room(event.room).name)

        REPORT_UNAVAILABLE = lambda report, user: _(
            '{user} reported unavailable room "{room_name}" at {reported_at}'
        ).format(
            user=user.username,
            room_name=Conf.get_room(report.room).name,
            reported_at=report.date,
        )

        REPORT_FREE = lambda report, user: _(
            '{user} reported free room "{room_name}" at {reported_at}'
        ).format(
            user=user.username,
            room_name=Conf.get_room(report.room).name,
            reported_at=report.date,
        )

        REPORT_BUSY = lambda report, user: _(
            '{user} reported busy room "{room_name}" at {reported_at}'
        ).format(
            user=user.username,
            room_name=Conf.get_room(report.room).name,
            reported_at=report.date,
        )
        OCCUPY_EDITED = lambda event, user: _(
            '{user} edited busy room "{room_name}" at {edited_at}'
        ).format(
            user=user.username,
            room_name=Conf.get_room(event.room).name,
            edited_at=event.end_date,
        )

        OCCUPY_DELETE = lambda event, user: _(
            '{user} deleted busy room "{room_name}"'
        ).format(user=user.username, room_name=Conf.get_room(event.room).name)

        REPORT_UNAVAILABLE_EVENT_EDITED = lambda event, user: _(
            '{user} edited unavailable room "{room_name}"'
        ).format(user=user.username, room_name=Conf.get_room(event.room).name)

        REPORT_UNAVAILABLE_EVENT_DELETED = lambda event, user: _(
            '{user} deleted unavailable room event "{room_name}"'
        ).format(user=user.username, room_name=Conf.get_room(event.room).name)


conf = Conf()

conf.__name__ = __name__
sys.modules[__name__] = conf
