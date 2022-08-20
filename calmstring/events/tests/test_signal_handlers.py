import sched
from django.test import override_settings
from utils.dates import tz_datetime
from django.utils import timezone
from .utils import TestCaseWithRooms, TestCaseForHuey
from huey.contrib.djhuey import HUEY
from datetime import timedelta
from .. import logic, tasks
from ..models import EventRoom

from freezegun import freeze_time


@freeze_time("2020-01-01 07:00:00")
class TestEventOccurrencesHandler(TestCaseWithRooms, TestCaseForHuey):
    def report_unavailable(self, recurrences=None):

        _recurrences = recurrences or self.clean_recurrence(
            "RRULE:FREQ=DAILY;INTERVAL=1"
        )

        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            "Room unavailable",
            "I don't know why, but it's daily",
            recurrences=_recurrences,
            emit_external_signals=False,
        )
        return event

    # Test method called by signdl set_event_occurrences
    @override_settings(CALMSTRING={"OCCURRENCES_PERIOD": 60 * 60 * 24 * 7})
    def test_occurrences_on_report_created(self):

        event = self.report_unavailable()
        event.refresh_from_db()

        occurrences = len(event.occurrences.keys())

        # couse current day is included
        self.assertEqual(occurrences, 8)

        scheduled = self.filterScheduledByFunc(
            tasks.call_set_event_occurrences
        )  # first should be our event

        self.assertEqual(len(scheduled), 1)

        self.assertEqual(scheduled[0].args[0], event.id)

        # next schedule should be in OCCURRENCES_PERIOD seconds on event.start_date
        next_schedule = timezone.make_naive(event.start_date) + timedelta(days=7)

        self.assertEqual(scheduled[0].eta, next_schedule)

    # Test method called by signdl set_event_occurrences
    @override_settings(CALMSTRING={"OCCURRENCES_PERIOD": 60 * 60 * 24 * 7})
    def test_occurrences_on_report_edited(self):

        event = self.report_unavailable()
        HUEY.flush()  # remove scheduled task

        event = logic.edit_report_unavailable_event(
            event,
            self.user,
            recurrences=self.clean_recurrence("RRULE:FREQ=WEEKLY;INTERVAL=1"),
        )
        event.refresh_from_db()

        occurrences = len(event.occurrences.keys())
        self.assertEqual(occurrences, 2)

        scheduled = self.filterScheduledByFunc(tasks.call_set_event_occurrences)

        self.assertEqual(scheduled[0].args[0], event.id)
        self.assertEqual(len(scheduled), 1)

        next_schedule = timezone.make_naive(event.start_date) + timedelta(days=7)
        self.assertEqual(scheduled[0].eta, next_schedule)

    @override_settings(CALMSTRING={"OCCURRENCES_PERIOD": 60 * 60 * 24 * 7})
    def test_occurrences_when_no_future_schedules(self):

        event = self.report_unavailable(
            recurrences=self.clean_recurrence(
                "RRULE:FREQ=WEEKLY;UNTIL=20200101T120000Z;INTERVAL=1"
            )
        )

        event.refresh_from_db()

        scheduled = self.filterScheduledByFunc(tasks.call_set_event_occurrences)

        self.assertEqual(len(scheduled), 1)


class TestCaseForNoRecurringAvailabilityHandler(TestCaseWithRooms, TestCaseForHuey):
    def assertTaskFuncOk(self, task):
        return self.assertScheduleTaskFuncEqual(
            task, tasks.call_set_event_room_availability
        )

    def assertWhenStartInPastAndEndInFuture(self, event, availability):
        scheduled = self.filterScheduledByFunc(tasks.call_set_event_room_availability)
        scheduled_on_end = scheduled[0]

        self.assertTaskFuncOk(scheduled_on_end)

        self.assertScheduleEtaEqual(scheduled_on_end, event.end_date)
        self.assertEqual(len(scheduled), 1)

        # check if call_set_event_was_called imidiately
        event.refresh_from_db()
        room_availability = event.room.availability
        self.assertEqual(room_availability, availability)

    def assertWhenStartInFuture(self, event):
        scheduled = self.filterScheduledByFunc(tasks.call_set_event_room_availability)
        scheduled_on_start = scheduled[0]
        scheduled_on_end = scheduled[1]

        self.assertEqual(len(scheduled), 2)

        self.assertScheduleEtaEqual(scheduled_on_start, event.start_date)
        self.assertScheduleEtaEqual(scheduled_on_end, event.end_date)


@freeze_time("2020-01-01 07:00:00")
class TestRoomAvailabilityHandlerForBusy(TestCaseForNoRecurringAvailabilityHandler):
    def test_when_start_date_in_the_future(self):
        start_date = tz_datetime(2020, 1, 1, 9, 0, 0)
        end_date = tz_datetime(2020, 1, 1, 12, 0, 0)
        event = logic.occupy_room(
            self.room1,
            self.user,
            start_date,
            end_date,
            "Test occupation",
            external_signals=False,
        )
        self.assertWhenStartInFuture(event)

    def test_when_start_date_in_the_past(self):
        start_date = tz_datetime(2020, 1, 1, 6, 0, 0)
        end_date = tz_datetime(2020, 1, 1, 8, 0, 0)

        event = logic.occupy_room(
            self.room1,
            self.user,
            start_date,
            end_date,
            "Test occupation",
            external_signals=False,
        )

        self.assertWhenStartInPastAndEndInFuture(event, EventRoom.Availabilities.BUSY)


@freeze_time("2020-01-01 07:00:00")
class TestRoomAvailabilityHandlerForUnavailableNotRecurring(
    TestCaseForNoRecurringAvailabilityHandler
):
    def test_when_start_date_in_the_future(self):
        start_date = tz_datetime(2020, 1, 1, 9, 0, 0)
        end_date = tz_datetime(2020, 1, 1, 12, 0, 0)
        event = logic.report_unavailable(
            self.room1,
            self.user,
            start_date,
            end_date,
            "Test Report unavailable start date in the future",
            external_signals=False,
        )
        self.assertWhenStartInFuture(event)

    def test_when_start_date_in_the_past(self):
        start_date = tz_datetime(2020, 1, 1, 6, 0, 0)
        end_date = tz_datetime(2020, 1, 1, 8, 0, 0)

        event = logic.report_unavailable(
            self.room1,
            self.user,
            start_date,
            end_date,
            "Test Report Unavailable start date in the past",
            external_signals=False,
        )
        self.assertWhenStartInPastAndEndInFuture(
            event, EventRoom.Availabilities.UNAVAILABLE
        )


@freeze_time("2020-01-01 08:00:00")
class TestRoomAvailabilityHandlerForRecurringEvents(TestCaseWithRooms, TestCaseForHuey):
    def test_when_started_in_the_past(self):
        start_date = tz_datetime(2019, 1, 1, 7, 0, 0)
        end_date = tz_datetime(2019, 1, 1, 10, 0, 0)
        event = logic.report_unavailable(
            self.room1,
            self.user,
            start_date,
            end_date,
            "Test Report unavailable start date in the future",
            recurrences=self.clean_recurrence("RRULE:FREQ=DAILY;INTERVAL=1"),
            external_signals=False,
        )

        scheduled_availability = self.filterScheduledByFunc(
            tasks.call_set_event_room_availability
        )

        self.assertEqual(len(scheduled_availability), 1)

        self.assertScheduleEtaEqual(
            scheduled_availability[0], tz_datetime(2020, 1, 1, 10, 0, 0)
        )

        scheduled_call_to_set_availability = self.filterScheduledByFunc(
            tasks.schedule_for_recurrent_event_call_set_event_room_availability
        )

        self.assertEqual(len(scheduled_call_to_set_availability), 1)

        self.assertScheduleEtaEqual(
            scheduled_call_to_set_availability[0], tz_datetime(2020, 1, 1, 10, 0, 0)
        )
