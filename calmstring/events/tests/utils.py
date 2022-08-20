from .deps import create_room
from ..models import EventRoom, Event
from utils.for_tests import TestCaseWithUsers
from recurrence.fields import RecurrenceField
from django.test import TestCase
from django.utils import timezone
from huey.contrib.djhuey import HUEY

from ..models import Event
from .. import logic
from utils.dates import tz_datetime


def create_event_room(name, description=""):
    return EventRoom.objects.create(room=create_room(name, description))


class TestCaseWithRooms(TestCaseWithUsers):
    def setUp(self):
        super().setUp()
        self.room1 = create_event_room(
            name="Test room 1",
            description="Test room 1 description",
        )
        self.room2 = create_event_room(name="room2")
        self.room3 = create_event_room(name="room3")

    @staticmethod
    def clean_recurrence(value):
        return RecurrenceField().clean(value, model_instance=None)

    def create_event(self, room=None, user=None, **kwargs):
        return Event.objects.create(
            room=room or self.room1, author=user or self.user, **kwargs
        )


class TestCaseForHuey(TestCase):
    def tearDown(self) -> None:
        HUEY.flush()
        return super().tearDown()

    @property
    def scheduled(self):

        scheduled = HUEY.scheduled()

        return sorted(scheduled, key=lambda x: x.eta)

    def assertScheduleEtaEqual(self, schedule, date):
        _date = date
        if timezone.is_aware(_date):
            _date = timezone.make_naive(_date)
        return self.assertEqual(schedule.eta, _date)

    def assertScheduleTaskFuncEqual(self, schedule_task, func):
        self.assertEqual(schedule_task.name, func.func.__name__)

    def filterScheduledByFunc(self, func):
        return list(filter(lambda tsk: tsk.name == func.func.__name__, self.scheduled))
