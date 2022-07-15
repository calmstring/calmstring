from datetime import datetime
from django.test import TestCase
from utils.for_tests import TestCaseWithUsers

# Create your tests here.
from .models import Room, Event
from . import exceptions, logic


class TestEventQuerySet(TestCaseWithUsers):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.room1 = Room.objects.create(name="room1")

        # Event hours: 10:00 - 12:00
        self.event1 = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=datetime(2020, 1, 1, 10, 0, 0),
            end_date=datetime(2020, 1, 1, 12, 0, 0),
        )

        # Event hours: 13:30 - 15:00
        self.event2 = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=datetime(2020, 1, 1, 13, 30, 0),
            end_date=datetime(2020, 1, 1, 15, 0, 0),
        )

    def test_no_overlaped_no_intersection(self):
        # Then check if there is no overlap:

        # Hours: 12:30 - 13:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 30, 0), datetime(2020, 1, 1, 13, 0, 0)
            ).count(),
            0,
        )

        # Hours : 09:00 - 10:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 9, 0, 0), datetime(2020, 1, 1, 10, 0, 0)
            ).count(),
            0,
        )

        # Hours : 12:00 - 13:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0), datetime(2020, 1, 1, 13, 0, 0)
            ).count(),
            0,
        )

        # Hours : 12:00 - 13:30
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0), datetime(2020, 1, 1, 13, 30, 0)
            ).count(),
            0,
        )

        # Hours : 15:00 - 16:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 15, 0, 0), datetime(2020, 1, 1, 16, 0, 0)
            ).count(),
            0,
        )

    def check_overlaped(self, intersection):
        # Hours : 10:00 - 12:00
        self.assertEquals(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 10, 0, 0),
                datetime(2020, 1, 1, 12, 0, 0),
                intersection=intersection,
            ).count(),
            1,
        )  # Case : 3

        # Hours : 10:30 - 13:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 10, 30, 0),
                datetime(2020, 1, 1, 13, 0, 0),
                intersection=intersection,
            ).count(),
            1,
        )  # Case : 1

        # Hours : 11:00 - 14:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 11, 0, 0),
                datetime(2020, 1, 1, 14, 0, 0),
                intersection=intersection,
            ).count(),
            2,
        )  # Case : 1,2

        # Hours: 13:00 - 15:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 13, 0, 0),
                datetime(2020, 1, 1, 15, 0, 0),
            ).count(),
            1,
        )  # Case : 4

        # Hours: 09:00 - 16:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 9, 0, 0),
                datetime(2020, 1, 1, 16, 0, 0),
                intersection=intersection,
            ).count(),
            2,
        )  # Case: 4

    def test_with_overlap_no_intersection(self):

        self.check_overlaped(intersection=False)

        # Hours: 12:00 - 13:31
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0),
                datetime(2020, 1, 1, 13, 31, 0),
            ).count(),
            1,
        )

    def test_no_overlap_with_intersection(self):
        # Hours: 12:30 - 13:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 30, 0),
                datetime(2020, 1, 1, 13, 0, 0),
                intersection=True,
            ).count(),
            0,
        )

        # Hours : 09:00 - 09:30
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 9, 0, 0),
                datetime(2020, 1, 1, 9, 30, 0),
                intersection=True,
            ).count(),
            0,
        )

    def test_overlap_with_intersection(self):
        self.check_overlaped(intersection=True)

        # Hours: 12:00 - 13:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0),
                datetime(2020, 1, 1, 13, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hours: 09:00 - 10:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 9, 0, 0),
                datetime(2020, 1, 1, 10, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hours: 12:00 - 13:30
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0),
                datetime(2020, 1, 1, 13, 30, 0),
                intersection=True,
            ).count(),
            2,
        )

    def test_no_overlap_with_no_end(self):

        # Hour 12:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0),
            ).count(),
            0,
        )
        # Hour: 09:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 9, 0, 0),
            ).count(),
            0,
        )

    def test_overlap_with_no_end(self):
        # Hour 11:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 11, 0, 0),
            ).count(),
            1,
        )

        # Hour 14:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 14, 0, 0),
            ).count(),
            1,
        )

    def test_overlap_with_no_end_with_intersection(self):
        # Hour 11:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 11, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hour 14:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 14, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hour 10:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 10, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hour 12:00
        self.assertEqual(
            Event.objects.overlaped_to(
                datetime(2020, 1, 1, 12, 0, 0),
                intersection=True,
            ).count(),
            1,
        )


class TestLogicOccupyRoom(TestCaseWithUsers):
    def setUp(self, *args, **kwargs):
        self.room1 = Room.objects.create(name="room1")
        self.room2 = Room.objects.create(name="room2")
        self.room3 = Room.objects.create(name="room3")

        super().setUp(*args, **kwargs)

    def test_occupy(self):
        event = logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=datetime(2020, 1, 1, 12, 0, 0),
            end_date=datetime(2020, 1, 1, 13, 0, 0),
        )
        self.assertTrue(isinstance(event, Event))

    def test_occupy_room_with_wrong_dates(self):
        date_start_after_end = datetime(2020, 1, 1, 12, 0, 0)
        date_end_before_start = datetime(2020, 1, 1, 10, 0, 0)

        with self.assertRaises(exceptions.ValidationError):

            logic.occupy_room(
                room=self.room1,
                user=self.user,
                start_date=date_start_after_end,
                end_date=date_end_before_start,
            )

    def test_occupy_when_user_has_event_not_ended(self):
        Event.objects.create(
            author=self.user,
            room=self.room1,
            start_date=datetime(2020, 1, 1, 12, 0, 0),
            end_date=None,
            availability=Event.Availabilities.BUSY,
        )

        with self.assertRaises(exceptions.NotEndedEventExists):
            logic.occupy_room(
                room=self.room1,
                user=self.user,
                start_date=datetime(2020, 1, 2, 12, 0, 0),
                end_date=datetime(2020, 1, 2, 13, 0, 0),
            )

    def create_test_events(self):
        # Event hours: 12:00 - 13:00
        Event.objects.create(
            author=self.user,
            room=self.room1,
            start_date=datetime(2020, 1, 1, 12, 0, 0),
            end_date=datetime(2020, 1, 1, 13, 0, 0),
            availability=Event.Availabilities.BUSY,
        )

        # Event hours: 14:00 - 16:00
        Event.objects.create(
            author=self.user,
            room=self.room2,
            start_date=datetime(2020, 1, 1, 14, 0, 0),
            end_date=datetime(2020, 1, 1, 16, 0, 0),
            availability=Event.Availabilities.BUSY,
        )

    def test_occupy_when_user_has_event_overlaped(self):
        def assertOccupy(start_date, end_date):
            with self.assertRaises(exceptions.OverlapedEventExists):
                logic.occupy_room(
                    room=self.room1,
                    user=self.user,
                    start_date=start_date,
                    end_date=end_date,
                )

        self.create_test_events()

        # Event hours: 12:00 - 13:00
        assertOccupy(datetime(2020, 1, 1, 12, 0, 0), datetime(2020, 1, 1, 13, 0, 0))

        # Event hours: 11:00 - 13:00
        assertOccupy(datetime(2020, 1, 1, 11, 0, 0), datetime(2020, 1, 1, 13, 0, 0))

        # Event hours 12:30 - 15:00
        assertOccupy(datetime(2020, 1, 1, 12, 30, 0), datetime(2020, 1, 1, 15, 0, 0))

        # Event hours 14:30 - 15:30
        assertOccupy(datetime(2020, 1, 1, 14, 30, 0), datetime(2020, 1, 1, 15, 30, 0))

    def test_when_events_are_not_overlaped(self):
        self.create_test_events() 
        # Event hours: 11:00 - 12:00
        event1 = logic.occupy_room(
            self.room1,
            self.user,
            datetime(2020, 1, 1, 11, 0, 0),
            datetime(2020, 1, 1, 12, 0, 0),
        )
        self.assertTrue(isinstance(event1, Event))
