from django.test import TestCase
from events.tests.utils import TestCaseWithRooms
from events import logic
from utils.dates import tz_datetime


# I wish someone would write a complete test for this
class TestEventChangeRevertedHandler(TestCaseWithRooms):
    def setUp(self):
        super().setUp()
        self.event_occupy = logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            name="Unitest",
            description="Unitest",
        )
        from changes.models import Change

        self.Change = Change

    def test_revert_occupy(self):

        self.assertEqual(self.Change.objects.all().count(), 1)

        first_change = self.Change.objects.all().first()

        logic.edit_occupy_room(
            event=self.event_occupy,
            user=self.user,
            name="Unitest tralal",
            description="Unitest",
        )
        self.event_occupy.refresh_from_db()
        self.assertEqual(self.event_occupy.name, "Unitest tralal")

        self.Change.reverted(to=first_change)

        self.event_occupy.refresh_from_db()

        self.assertEqual(self.event_occupy.name, "Unitest")


class TestCreateEventRoomHandler(TestCase):
    def test_create_room(self):
        from rooms.logic import create_room
        from events.models import EventRoom

        room = create_room(name="Room1", description="Room 1 description")

        event_room = EventRoom.objects.filter(room=room).first()

        self.assertTrue(isinstance(event_room, EventRoom))
