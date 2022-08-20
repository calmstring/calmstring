from django.utils.translation import gettext_lazy as _
from . import exceptions

import recurrence


def validate_recurrence(start_date, end_date, recurrences):
    """Validator for recurrent event


    Args:
        start_date (_type_): _description_
        end_date (_type_): _description_
        recurrences (_type_): _description_

    Raises:
        exceptions.ValidationError: When recurrences frequently is faster than DAILY
        exceptions.ValidationError: When recurrences are byhour
        exceptions.ValidationError: When recurrences are byminute
        exceptions.ValidationError: When recurrences are bysecond
        exceptions.ValidationError: When recurrences are byday, but not inludes start_date day

    Returns:
        _type_: _description_
    """
    for rrule in recurrences.rrules:
        if rrule.freq in [
            recurrence.HOURLY,
            recurrence.MINUTELY,
            recurrence.SECONDLY,
        ]:
            raise exceptions.ValidationError(_("Max frequency is daily"))
        if rrule.byhour:
            raise exceptions.ValidationError(_("Recurrences are not hourly"))
        if rrule.byminute:
            raise exceptions.ValidationError(_("Recurrences are not minutly"))
        if rrule.bysecond:
            raise exceptions.ValidationError(_("Recurrences are not secondly"))

        if rrule.byday:
            if not start_date.weekday() in list(
                map(lambda rd: rd.weekday, rrule.byday)
            ):
                raise exceptions.ValidationError(
                    _("By day rule must include start date day")
                )
        return True


def validate_dates(start_date, end_date, max_duration: int = None):
    """Check if event start is not after end,and optionally if duration is not too long

    Args:
        start_date (datetime): _description_
        end_date (datetime): _description_
        max_duration (int, optional): Event max duration. Defaults to None.

    Raises:
        exceptions.ValidationError: When end is before start
        exceptions.ValidationError: When event duration is longer than max_duration param
    """
    if start_date >= end_date:
        raise exceptions.ValidationError(_("End date is before start date"))

    if max_duration:

        if (end_date - start_date).seconds > max_duration:
            raise exceptions.ValidationError(_("Too long period"))

    return True
