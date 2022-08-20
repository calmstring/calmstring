from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from utils.dates import tz_datetime

from .utils import TestCaseWithRooms
from .. import logic
from ..models import Event

User = get_user_model()


class BaseTestCase(TestCaseWithRooms):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user.role = User.Roles.NORMAL
        self.user.save()


class TestOccupyRoomViewset(BaseTestCase):
    def test_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("OccupyRoomViewset-list"),
            {
                "room": self.room1.uuid,
                "start_date": tz_datetime(2022, 1, 1, 10, 0, 0),
                "end_date": tz_datetime(2022, 1, 1, 11, 0, 0),
                "name": "Test event",
                "description": "Test description",
            },
        )
        self.assertTrue(status.is_success(response.status_code))

    def test_partial_update(self):
        event = logic.occupy_room(
            self.room1,
            self.user,
            tz_datetime(2022, 1, 1, 10, 0, 0),
            tz_datetime(2022, 1, 1, 11, 0, 0),
            "Test event",
            "Test description",
            emit_signals=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("OccupyRoomViewset-detail", args=[event.uuid]),
            {
                "start_date": tz_datetime(2022, 1, 1, 10, 30, 0),
                "name": "Test event 2",
                "room": "1322",
            },
        )
        self.assertTrue(status.is_success(response.status_code))
        event.refresh_from_db()
        self.assertEqual(event.start_date, tz_datetime(2022, 1, 1, 10, 30, 0))
        self.assertEqual(event.name, "Test event 2")
        self.assertEqual(event.room, self.room1)

    def test_destroy(self):
        event = logic.occupy_room(
            self.room1,
            self.user,
            tz_datetime(2022, 1, 1, 10, 0, 0),
            tz_datetime(2022, 1, 1, 11, 0, 0),
            "Test event",
            "Test description",
            emit_signals=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("OccupyRoomViewset-detail", args=[event.uuid]),
            {},
        )
        self.assertTrue(status.is_success(response.status_code))

        existing_events = Event.objects.existing().count()
        self.assertEqual(existing_events, 0)

    def test_free(self):
        event = logic.occupy_room(
            self.room1,
            self.user,
            tz_datetime(2022, 1, 1, 10, 0, 0),
            None,
            "Test event",
            "Test description",
            emit_signals=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("OccupyRoomViewset-free", args=[event.uuid]),
            {"end_date": tz_datetime(2022, 1, 1, 11, 0, 0)},
        )

        self.assertTrue(status.is_success(response.status_code))
        event.refresh_from_db()
        self.assertEqual(event.end_date, tz_datetime(2022, 1, 1, 11, 0, 0))


class TestEventUnavailableRoomViewset(BaseTestCase):
    def test_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("EventUnavailableRoomViewset-list"),
            {
                "room": self.room1.uuid,
                "start_date": tz_datetime(2022, 1, 1, 10, 0, 0),
                "end_date": tz_datetime(2022, 1, 1, 18, 0, 0),
                "name": "Test event",
                "description": "Test description",
                "recurrences": "RRULE:FREQ=DAILY",
            },
        )
        self.assertTrue(status.is_success(response.status_code))

    def test_partial_update(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2022, 1, 1, 10, 0, 0),
            tz_datetime(2022, 1, 1, 18, 0, 0),
            "Test event",
            "Test description",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("EventUnavailableRoomViewset-detail", args=[event.uuid]),
            {
                "start_date": tz_datetime(2022, 1, 1, 10, 30, 0),
                "recurrences": "RRULE:FREQ=DAILY;COUNT=2",
                "room": "cant change room",
            },
        )
        self.assertTrue(status.is_success(response.status_code))
        event.refresh_from_db()
        self.assertEqual(event.start_date, tz_datetime(2022, 1, 1, 10, 30, 0))
        self.assertEqual(event.room, self.room1)

    def test_destroy(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2022, 1, 1, 10, 0, 0),
            tz_datetime(2022, 1, 1, 18, 0, 0),
            "Test event",
            "Test description",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("EventUnavailableRoomViewset-detail", args=[event.uuid]), {}
        )
        self.assertTrue(status.is_success(response.status_code))

        existing_events = Event.objects.existing().count()
        self.assertEqual(existing_events, 0)
