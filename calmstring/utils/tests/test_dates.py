from datetime import datetime
from ..dates import is_all_day
from django.test import SimpleTestCase


class Test_is_all_day(SimpleTestCase):
    def test_one_day(self):
        self.assertEqual(
            is_all_day(datetime(2020, 1, 1), datetime(2020, 1, 2)),
            (
                True,
                datetime(1, 1, 2) - datetime(1, 1, 1),
            ),
        )

    def test_few_days(self):
        self.assertEqual(
            is_all_day(datetime(2020, 1, 1), datetime(2020, 1, 3)),
            (True, datetime(1, 1, 3) - datetime(1, 1, 1)),
        )

    def test_when_not_is_all_day(self):
        self.assertEqual(
            is_all_day(datetime(2020, 1, 1), datetime(2020, 1, 2, 1)),
            (False, datetime(1, 1, 2, 1) - datetime(1, 1, 1)),
        )
