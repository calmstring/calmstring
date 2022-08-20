from datetime import datetime
from django.utils import timezone


def is_all_day(start_date: datetime, end_date: datetime) -> tuple:
    """_summary_

    Args:
        start_date (datetime): Start date of event.
        end_date (datetime): End date of event

    Returns:
        tuple: (is_all_day, timedelta)
    """
    tdelta = abs(end_date - start_date)

    _is_all_day = tdelta.days and not tdelta.seconds

    return (_is_all_day, tdelta)


def tz_datetime(*args, **kwargs):
    return timezone.make_aware(datetime(*args, **kwargs))
