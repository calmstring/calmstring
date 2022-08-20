from django.test import TestCase

from utils.dates import tz_datetime

from datetime import datetime

# Create your tests here.
from ..models import EventRoom, Report, Event
from .. import exceptions, logic
from .utils import TestCaseWithRooms

import recurrence


class TestIsRecurrenceValid(TestCaseWithRooms):
    pass


class TestOccupyRoom(TestCaseWithRooms):
    def test_occupy(self):
        event = logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            emit_signals=False,
            name="Unitest",
            description="Unitest",
        )
        self.assertTrue(isinstance(event, Event))
        self.assertEqual(event.room, self.room1)
        self.assertEqual(event.author, self.user)
        self.assertEqual(event.start_date, tz_datetime(2020, 1, 1, 12, 0, 0))
        self.assertEqual(event.end_date, tz_datetime(2020, 1, 1, 13, 0, 0))
        self.assertEqual(event.name, "Unitest")
        self.assertEqual(event.description, "Unitest")

    def test_occupy_when_user_has_event_not_ended(self):
        Event.objects.create(
            author=self.user,
            room=self.room1,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=None,
            availability=Event.Availabilities.BUSY,
        )

        with self.assertRaises(exceptions.NotEndedEventExists):
            logic.occupy_room(
                room=self.room1,
                user=self.user,
                start_date=tz_datetime(2020, 1, 2, 12, 0, 0),
                end_date=tz_datetime(2020, 1, 2, 13, 0, 0),
                emit_signals=False,
            )

    def create_test_events(self):
        # Event hours: 12:00 - 13:00
        Event.objects.create(
            author=self.user,
            room=self.room1,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            availability=Event.Availabilities.BUSY,
        )

        # Event hours: 14:00 - 16:00
        Event.objects.create(
            author=self.user,
            room=self.room2,
            start_date=tz_datetime(2020, 1, 1, 14, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 16, 0, 0),
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
                    emit_signals=False,
                )

        self.create_test_events()

        # Event hours: 12:00 - 13:00
        assertOccupy(
            tz_datetime(2020, 1, 1, 12, 0, 0), tz_datetime(2020, 1, 1, 13, 0, 0)
        )

        # Event hours: 11:00 - 13:00
        assertOccupy(
            tz_datetime(2020, 1, 1, 11, 0, 0), tz_datetime(2020, 1, 1, 13, 0, 0)
        )

        # Event hours 12:30 - 15:00
        assertOccupy(
            tz_datetime(2020, 1, 1, 12, 30, 0), tz_datetime(2020, 1, 1, 15, 0, 0)
        )

        # Event hours 14:30 - 15:30
        assertOccupy(
            tz_datetime(2020, 1, 1, 14, 30, 0), tz_datetime(2020, 1, 1, 15, 30, 0)
        )

    def test_when_events_are_not_overlaped(self):
        self.create_test_events()
        # Event hours: 11:00 - 12:00
        event1 = logic.occupy_room(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 11, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            emit_signals=False,
        )
        self.assertTrue(isinstance(event1, Event))


class TestFreeRoom(TestCaseWithRooms):
    def setUp(self, *args, **kwargs):

        super().setUp(*args, **kwargs)

        self.not_ended_event = Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=tz_datetime(2020, 1, 1, 8, 0, 0),
            availability=Event.Availabilities.BUSY,
        )

    def test_when_user_have_multiple_not_ended_events(self):
        Event.objects.create(
            room=self.room1,
            author=self.user,
            start_date=tz_datetime(2020, 1, 2, 8, 0, 0),
            availability=Event.Availabilities.BUSY,
        )
        with self.assertRaises(exceptions.MultipleNotEndedEventsExists):
            logic.free_room(
                self.room1,
                self.user,
                tz_datetime(2020, 1, 1, 9, 0, 0),
                emit_signals=False,
            )

    def test_when_user_does_not_have_not_ended_event(self):
        self.not_ended_event.end_date = tz_datetime(2020, 1, 1, 9, 0, 0)

        self.not_ended_event.save()

        with self.assertRaises(exceptions.NotEndedEventDoesNotExist):
            logic.free_room(
                self.room1,
                self.user,
                tz_datetime(2020, 1, 1, 9, 0, 0),
                emit_signals=False,
            )

    def test_freeroom(self):
        event = logic.free_room(
            self.room1, self.user, tz_datetime(2020, 1, 1, 9, 0, 0), emit_signals=False
        )
        self.assertEqual(event.end_date, tz_datetime(2020, 1, 1, 9, 0, 0))


class TestReportUnavailable(TestCaseWithRooms):
    def test_report_with_no_end_date(self):
        response = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            name="Teacher in room",
            description="I don't know who is it",
            emit_signals=False,
        )
        self.assertTrue(isinstance(response, Report))

    def test_report_with_all_day_event(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1),
            tz_datetime(2020, 1, 2),
            emit_signals=False,
        )
        self.assertTrue(isinstance(event, Event))
        self.assertTrue(event.is_all_day)

    def test_report_with_recurrences(self):
        # rfc 2445/5545
        recurrences = self.clean_recurrence("RRULE:FREQ=DAILY;UNTIL=20210101T000000Z")

        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            name="Teacher in room from 8:00 to 12:00 - I think",
            recurrences=recurrences,
            emit_signals=False,
        )
        self.assertTrue(event.is_recurring)


class TestReportFree(TestCaseWithRooms):
    def test_report_free(self):
        report = logic.report_free(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            name="Teacher in room from 8:00 to 12:00 - I think",
            emit_signals=False,
        )
        self.assertTrue(isinstance(report, Report))


class TestReportBusy(TestCaseWithRooms):
    def test_report_busy(self):
        report = logic.report_busy(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            name="Someone is in room",
        )
        self.assertTrue(isinstance(report, Report))

    def test_report_busy_with_reported_users(self):
        self.create_user("user2")
        self.create_user("user3")

        report = logic.report_busy(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            reported_users=[self.user2, self.user3],
            name="There are in room",
        )

        self.assertTrue(isinstance(report, Report))
        self.assertEqual(report.reported_users.count(), 2)


class TestEditOccupyRoom(TestCaseWithRooms):
    def test_edit_occupy(self):
        event = logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            emit_signals=False,
        )

        event = logic.edit_occupy_room(
            event=event,
            user=self.superuser,
            name="Unitest",
            description="Unitest",
            emit_signals=False,
        )

        self.assertEqual(event.name, "Unitest")
        self.assertEqual(event.description, "Unitest")

    def test_edit_occupy_dates_overlaped(self):
        logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            emit_signals=False,
        )
        event = logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=tz_datetime(2020, 1, 1, 10, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 11, 0, 0),
            emit_signals=False,
        )

        with self.assertRaises(exceptions.OverlapedEventExists):
            logic.edit_occupy_room(
                event=event,
                user=self.user,
                end_date=tz_datetime(2020, 1, 1, 12, 30, 0),
                emit_signals=False,
            )

    def test_force_edit(self):
        event = logic.occupy_room(
            room=self.room1,
            user=self.user,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            emit_signals=False,
        )

        event.name = "Unitest123123"

        event = logic.edit_occupy_room(
            event=event,
            user=self.superuser,
            emit_signals=False,
            force_edit=True,
        )

        event.refresh_from_db()
        self.assertEqual(event.name, "Unitest123123")


class TestDeleteOccupyRoom(TestCaseWithRooms):
    def test_delete(self):
        event = logic.occupy_room(
            user=self.user,
            room=self.room1,
            start_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 13, 0, 0),
            emit_signals=False,
        )
        event = logic.delete_occupy_room(event, self.superuser, emit_signals=False)

        self.assertEqual(event.is_deleted, True)


class TestEditReportUnavailableEvent(TestCaseWithRooms):
    def test_edit(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            emit_signals=False,
        )

        event = logic.edit_report_unavailable_event(
            event,
            self.superuser,
            name="Unitest",
            description="Unitest",
            emit_signals=False,
        )

        self.assertEqual(event.name, "Unitest")
        self.assertEqual(event.description, "Unitest")

    def test_edit_add_reccurrences(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            emit_signals=False,
        )
        event = logic.edit_report_unavailable_event(
            event,
            self.superuser,
            name="Unitest",
            description="Unitest",
            recurrences=self.clean_recurrence("RRULE:FREQ=DAILY"),
            emit_signals=False,
        )
        self.assertTrue(event.is_recurring)

    def test_edit_remove_reccurrences(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            recurrences=self.clean_recurrence("RRULE:FREQ=DAILY"),
            emit_signals=False,
        )
        event = logic.edit_report_unavailable_event(
            event,
            self.user,
            recurrences=None,
            emit_signals=False,
        )
        self.assertFalse(event.is_recurring)


class TestDeleteReportUnavailableEvent(TestCaseWithRooms):
    def test_delete(self):
        event = logic.report_unavailable(
            self.room1,
            self.user,
            tz_datetime(2020, 1, 1, 8, 0, 0),
            tz_datetime(2020, 1, 1, 12, 0, 0),
            emit_signals=False,
        )
        event = logic.delete_report_unavailable_event(
            event, self.superuser, emit_signals=False
        )

        self.assertEqual(event.is_deleted, True)


class TestSetEventOccurrences(TestCaseWithRooms):
    def setUp(self):
        super().setUp()
        self.event1 = self.create_event(
            availability=Event.Availabilities.UNAVAILABLE,
            start_date=tz_datetime(2020, 1, 1, 8, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 12, 0, 0),
        )

    def test_when_is_not_recurring(self):
        next_schedule = logic.set_event_occurrences(self.event1, emit_signals=False)
        self.assertIsNone(next_schedule)

    def test_with_weekly_recurring(self):
        self.event1.recurrences = recurrence.Recurrence(
            rrules=[recurrence.Rule(freq=recurrence.WEEKLY)]
        )
        self.event1.is_recurring = True
        self.event1.save()
        next_schedule = logic.set_event_occurrences(
            self.event1,
            dtstart=tz_datetime(2020, 1, 1, 8, 0, 0),
            period=60 * 60 * 24 * 6,  # In fact 7 will couse in 8 days
            emit_signals=False,
        )
        self.assertEqual(next_schedule, tz_datetime(2020, 1, 7, 8, 0, 0))

    def test_with_ended_recurring(self):
        self.event1.recurrences = recurrence.Recurrence(
            rrules=[
                recurrence.Rule(recurrence.WEEKLY, until=datetime(2020, 1, 1, 0, 0, 0))
            ]
        )
        self.event1.is_recurring = True
        self.event1.save()

        next_schedule = logic.set_event_occurrences(
            self.event1,
            dtstart=tz_datetime(2020, 1, 1, 8, 0, 0),
            period=60 * 60 * 24 * 6,
            emit_signals=False,
        )
        self.assertIsNone(next_schedule)


class TestGetEventRoomAvailability(TestCaseWithRooms):
    def setUp(self):
        super().setUp()

        # add events

        # 8-12 unavailable
        self.create_event(
            start_date=tz_datetime(2020, 1, 1, 8, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 12, 0, 0),
            availability=Event.Availabilities.UNAVAILABLE,
        )
        # 9-11 busy
        self.create_event(
            start_date=tz_datetime(2020, 1, 1, 9, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 11, 0, 0),
            availability=Event.Availabilities.BUSY,
        )

        # 15-16 unavailable #
        recc_event = self.create_event(
            start_date=tz_datetime(2019, 1, 1, 15, 0, 0),
            end_date=tz_datetime(2019, 1, 1, 16, 0, 0),
            availability=Event.Availabilities.UNAVAILABLE,
            is_recurring=True,
            recurrences=self.clean_recurrence("RRULE:FREQ=DAILY"),
        )
        # This part is crucial for recurrent events
        recc_occur = recc_event.get_occurrences(
            datetime(2020, 1, 1, 0, 0, 0), datetime(2020, 1, 7, 0, 0, 0)
        )
        recc_event.occurrences = Event.prepare_occurrences_for_db(recc_occur)
        recc_event.save()
        # 15-16 unavailable #

        # 18-20 busy
        self.create_event(
            start_date=tz_datetime(2020, 1, 1, 18, 0, 0),
            end_date=tz_datetime(2020, 1, 1, 20, 0, 0),
            availability=Event.Availabilities.BUSY,
        )

    def test_when_unknown(self):
        status = logic.get_event_room_availability(
            self.room1, tz_datetime(2020, 1, 1, 10, 0, 0)
        )
        self.assertEqual(status, EventRoom.Availabilities.UNKNOWN)

    def test_when_free(self):
        status = logic.get_event_room_availability(
            self.room1, tz_datetime(2020, 1, 1, 13, 0, 0)
        )
        self.assertEqual(status, EventRoom.Availabilities.FREE)

    def test_when_unavailable(self):
        status = logic.get_event_room_availability(
            self.room1, tz_datetime(2020, 1, 1, 15, 0, 0)
        )
        self.assertEqual(status, EventRoom.Availabilities.UNAVAILABLE)

    def test_when_busy_on_event_start(self):
        status = logic.get_event_room_availability(
            self.room1, tz_datetime(2020, 1, 1, 18, 0, 0)
        )
        self.assertEqual(status, EventRoom.Availabilities.BUSY)

    def test_free_on_event_end(self):
        status = logic.get_event_room_availability(
            self.room1, tz_datetime(2020, 1, 1, 20, 0, 0)
        )
        self.assertEqual(status, EventRoom.Availabilities.FREE)
