from django.test import TestCase
from .. import logic
from ..models import Room


class TestCreateRoom(TestCase):
    def test_create(self):
        name = "Room 1"
        description = "Room 1 description"
        room = logic.create_room(name=name, description=description)

        self.assertTrue(isinstance(room, Room))

        self.assertEqual(room.name, name)
        self.assertEqual(room.description, description)
