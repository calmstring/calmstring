from django.test import TestCase
from rooms import logic
from utils.constant import AvailabilitiesBase


class TestRoomAvailability(TestCase):
    def test_availability_no_event_room(self):
        room = logic.create_room(
            name="room1", description="room1 description", emit_signals=False
        )
        availability = room.availability

        self.assertEqual(availability, AvailabilitiesBase.UNKNOWN)

    def test_availability_with_event_room(self):
        room = logic.create_room(name="room1", description="room1 description")

        event_room = room.events_room
        event_room.availability = AvailabilitiesBase.BUSY
        event_room.save()

        room.refresh_from_db()

        self.assertEqual(room.availability, AvailabilitiesBase.BUSY)

    def test_events_room_uuid_no_event_room(self):
        room = logic.create_room(
            name="room1", description="room1 description", emit_signals=False
        )
        self.assertIsNone(room.events_room_uuid)

    def test_events_room_uuid(self):
        room = logic.create_room(name="room1", description="room1 description")

        self.assertIsNotNone(room.events_room_uuid)
