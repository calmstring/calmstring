from datetime import datetime, date
from ..models import Event
from utils.for_tests import TestCaseWithUsers
from utils.dates import tz_datetime
from recurrence.fields import RecurrenceField
from .. import exceptions

from .utils import create_event_room


class TestCaseWithEvents(TestCaseWithUsers):
    @staticmethod
    def clean_recurrence(value):
        return RecurrenceField().clean(value, model_instance=None)

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.room1 = create_event_room(name="room1")

        # Event hours: 10:00 - 12:00
        self.event1 = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=tz_datetime(2020, 1, 1, 10, 0, 0),  # wendesday, 10:00
            end_date=tz_datetime(2020, 1, 1, 12, 0, 0),
        )

        # Event hours: 13:30 - 15:00
        self.event2 = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=tz_datetime(2020, 1, 1, 13, 30, 0),
            end_date=tz_datetime(2020, 1, 1, 15, 0, 0),
        )


class TestEvent(TestCaseWithEvents):
    def _test_validate_occurences(self):
        self.event1.is_recurring = True
        self.event1.save()
        self.event1.recurrences = self.clean_recurrence("RRULE:FREQ=HOURLY;INTERVAL=1")
        with self.assertRaises(exceptions.ValidationError):
            self.event1.validate_recurrences()

        self.event1.recurrences = self.clean_recurrence(
            "RRULE:FREQ=SECONDLY;INTERVAL=1"
        )
        with self.assertRaises(exceptions.ValidationError):
            self.event1.validate_recurrences()

        self.event1.recurrences = self.clean_recurrence("RRULE:FREQ=WEEKLY;BYDAY=MO")
        with self.assertRaises(exceptions.ValidationError):
            self.event1.validate_recurrences()

        self.event1.recurrences = self.clean_recurrence("RRULE:FREQ=WEEKLY;BYDAY=WE")
        self.assertTrue(self.event1.validate_recurrences())

    def test_set_next_occurrence(self):
        self.event1.recurrences = self.clean_recurrence("RRULE:FREQ=DAILY;INTERVAL=1")
        self.event1.is_recurring = True
        self.event1.save()
        todays_date = datetime(2020, 1, 3, 0, 0, 0).date()

        next_occurence = self.event1.set_next_occurrence(date_from=todays_date)

        self.event1.refresh_from_db()

        self.assertEqual(next_occurence, todays_date)
        self.assertEqual(self.event1.next_occurrence, todays_date)

    def test_set_next_occurrence_when_there_no_recurrence(self):
        # yeasterday = datetime(2020, 1, 1, 0, 0, 0).strftime("%Y%m%dT000000Z")
        yeasterday = "20200101T000000Z"
        self.event1.recurrences = self.clean_recurrence(
            f"RRULE:FREQ=DAILY;UNTIL={yeasterday}"
        )
        self.event1.is_recurring = True
        self.event1.save()

        next_occurence = self.event1.set_next_occurrence(
            date_from=datetime(2020, 1, 2, 0, 0, 0)
        )

        self.assertEqual(next_occurence, None)
        self.assertEqual(self.event1.next_occurrence, None)

    def test_get_occurrences(self):
        self.event1.recurrences = self.clean_recurrence("RRULE:FREQ=DAILY;INTERVAL=1")
        self.event1.is_recurring = True
        self.event1.save()

        month_occurrences = self.event1.get_occurrences(
            date_from=datetime(2020, 1, 1, 0, 0, 0),
            date_to=datetime(2020, 1, 31, 0, 0, 0),
            dtstart=datetime(2020, 1, 1, 0, 0, 0),
        )
        self.assertEqual(len(month_occurrences), 31)

        two_days_occurrences = self.event1.get_occurrences(
            date_from=datetime(2020, 1, 1, 0, 0, 0),
            date_to=datetime(2020, 1, 2, 0, 0, 0),
            dtstart=datetime(2020, 1, 1, 0, 0, 0),
        )
        self.assertEqual(len(two_days_occurrences), 2)

    def test_get_occurrences_when_there_no_recurrence(self):
        yeasterday = "20190101T000000Z"
        self.event1.recurrences = self.clean_recurrence(
            f"RRULE:FREQ=DAILY;UNTIL={yeasterday}"
        )
        self.event1.is_recurring = True
        self.event1.save()

        month_occurrences = self.event1.get_occurrences(
            datetime(2020, 1, 2, 0, 0, 0),
            datetime(2020, 1, 31, 0, 0, 0),
            dtstart=datetime(2020, 1, 1, 0, 0, 0),
        )
        self.assertEqual(len(month_occurrences), 0)

    def test_prepare_occurrences_for_db(self):
        occurrences = [
            tz_datetime(2020, 1, 1, 0, 0, 0),
            tz_datetime(2020, 1, 8, 1, 2, 3),
        ]
        prepared_for_db = Event.prepare_occurrences_for_db(occurrences)

        self.assertEqual(
            prepared_for_db,
            {
                "2020-01-01": True,
                "2020-01-08": True,
            },
        )

    def test_prepare_occurrences_from_db(self):
        self.event1.occurrences = {
            "2020-01-01": True,
            "2020-01-08": True,
        }
        self.event1.save()
        self.assertEqual(
            self.event1.prepare_occurrences_from_db(),
            [
                date(2020, 1, 1),
                date(2020, 1, 8),
            ],
        )


class TestEventQuerySetOverlapTo(TestCaseWithEvents):
    def setUp(self):
        super().setUp()
        # add some recurring events
        self.event3 = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=tz_datetime(2019, 1, 1, 17, 0, 0),
            end_date=tz_datetime(2019, 1, 1, 18, 0, 0),
            is_recurring=True,
            recurrences=self.clean_recurrence("RRULE:FREQ=DAILY"),
            availability=Event.Availabilities.UNAVAILABLE,
        )

        self.event4 = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=tz_datetime(2019, 1, 1, 8, 0, 0),
            end_date=tz_datetime(2019, 1, 1, 8, 30, 0),
            is_recurring=True,
            recurrences=self.clean_recurrence("RRULE:FREQ=DAILY"),
            availability=Event.Availabilities.UNAVAILABLE,
        )

        ## This part is crucial for recurrent events
        event3_occ = self.event3.get_occurrences(
            datetime(2020, 1, 1, 0, 0, 0), datetime(2020, 1, 7, 0, 0, 0)
        )
        self.event3.occurrences = Event.prepare_occurrences_for_db(event3_occ)
        self.event3.save()

        event4_occ = self.event4.get_occurrences(
            datetime(2020, 1, 1, 0, 0, 0), datetime(2020, 1, 7, 0, 0, 0)
        )
        self.event4.occurrences = Event.prepare_occurrences_for_db(event4_occ)
        self.event4.save()

    def test_no_overlaped_no_intersection(self):
        # Then check if there is no overlap:

        # Hours: 12:30 - 13:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 30, 0), tz_datetime(2020, 1, 1, 13, 0, 0)
            )
            .count(),
            0,
        )

        # Hours : 09:00 - 10:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 9, 0, 0), tz_datetime(2020, 1, 1, 10, 0, 0)
            )
            .count(),
            0,
        )

        # Hours : 12:00 - 13:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0), tz_datetime(2020, 1, 1, 13, 0, 0)
            )
            .count(),
            0,
        )

        # Hours : 12:00 - 13:30
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0), tz_datetime(2020, 1, 1, 13, 30, 0)
            )
            .count(),
            0,
        )

        # Hours : 15:00 - 16:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 15, 0, 0), tz_datetime(2020, 1, 1, 16, 0, 0)
            )
            .count(),
            0,
        )

    def check_overlaped(self, intersection):

        # Hours: 07:00 - 08:10
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 7, 0, 0), tz_datetime(2020, 1, 1, 8, 10, 0)
            )
            .count(),
            1,
        )  # Case 1,2

        # Hours 17:00 - 18:00
        self.assertEquals(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 17, 0, 0),
                tz_datetime(2020, 1, 1, 18, 0, 0),
                intersection=intersection,
            )
            .count(),
            1,
        )  # Case : 3

        # Hours : 10:00 - 12:00
        self.assertEquals(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 10, 0, 0),
                tz_datetime(2020, 1, 1, 12, 0, 0),
                intersection=intersection,
            )
            .count(),
            1,
        )  # Case : 3

        # Hours : 10:30 - 13:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 10, 30, 0),
                tz_datetime(2020, 1, 1, 13, 0, 0),
                intersection=intersection,
            )
            .count(),
            1,
        )  # Case : 1

        # Hours : 11:00 - 14:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 11, 0, 0),
                tz_datetime(2020, 1, 1, 14, 0, 0),
                intersection=intersection,
            )
            .count(),
            2,
        )  # Case : 1,2

        # Hours: 13:00 - 15:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 13, 0, 0),
                tz_datetime(2020, 1, 1, 15, 0, 0),
            )
            .count(),
            1,
        )  # Case : 4

        # Hours: 09:00 - 16:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 9, 0, 0),
                tz_datetime(2020, 1, 1, 16, 0, 0),
                intersection=intersection,
            )
            .count(),
            2,
        )  # Case: 4

        # Hours: 07:00 - 19:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 7, 0, 0),
                tz_datetime(2020, 1, 1, 19, 0, 0),
                intersection=intersection,
            )
            .count(),
            4,
        )  # Case: 4

    def test_with_overlap_no_intersection(self):

        self.check_overlaped(intersection=False)

        # Hours: 12:00 - 13:31
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0),
                tz_datetime(2020, 1, 1, 13, 31, 0),
            )
            .count(),
            1,
        )

    def test_no_overlap_with_intersection(self):
        # Hours: 12:30 - 13:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 30, 0),
                tz_datetime(2020, 1, 1, 13, 0, 0),
                intersection=True,
            )
            .count(),
            0,
        )

        # Hours : 09:00 - 09:30
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 9, 0, 0),
                tz_datetime(2020, 1, 1, 9, 30, 0),
                intersection=True,
            )
            .count(),
            0,
        )

    def test_overlap_with_intersection(self):
        self.check_overlaped(intersection=True)

        # Hours: 12:00 - 13:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0),
                tz_datetime(2020, 1, 1, 13, 0, 0),
                intersection=True,
            )
            .count(),
            1,
        )

        # Hours: 09:00 - 10:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 9, 0, 0),
                tz_datetime(2020, 1, 1, 10, 0, 0),
                intersection=True,
            )
            .count(),
            1,
        )

        # Hours: 12:00 - 13:30
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0),
                tz_datetime(2020, 1, 1, 13, 30, 0),
                intersection=True,
            )
            .count(),
            2,
        )

    def test_no_overlap_with_no_end(self):

        # Hour 12:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0),
            )
            .count(),
            0,
        )
        # Hour: 09:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 9, 0, 0),
            )
            .count(),
            0,
        )

    def test_overlap_with_no_end(self):
        # Hour 11:00
        self.assertEqual(
            Event.objects.existing()
            .overlaped_to(
                tz_datetime(2020, 1, 1, 11, 0, 0),
            )
            .count(),
            1,
        )

        # Hour 14:00
        self.assertEqual(
            Event.objects.overlaped_to(
                tz_datetime(2020, 1, 1, 14, 0, 0),
            ).count(),
            1,
        )

    def test_overlap_with_no_end_with_intersection(self):
        # Hour 11:00
        self.assertEqual(
            Event.objects.overlaped_to(
                tz_datetime(2020, 1, 1, 11, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hour 14:00
        self.assertEqual(
            Event.objects.overlaped_to(
                tz_datetime(2020, 1, 1, 14, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hour 10:00
        self.assertEqual(
            Event.objects.overlaped_to(
                tz_datetime(2020, 1, 1, 10, 0, 0),
                intersection=True,
            ).count(),
            1,
        )

        # Hour 12:00
        self.assertEqual(
            Event.objects.overlaped_to(
                tz_datetime(2020, 1, 1, 12, 0, 0),
                intersection=True,
            ).count(),
            1,
        )
