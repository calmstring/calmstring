import django.dispatch


"""
    kwargs:
        - event: Event instance
"""
occupy_created = django.dispatch.Signal()
occupy_ended = django.dispatch.Signal()
occupy_edited = django.dispatch.Signal()
occupy_deleted = django.dispatch.Signal()


"""

    kwargs:
        - event: Event instance. Default None
        - report: Report instance. Default None
    Kwarg depends of report type
"""
report_unavailable_created = django.dispatch.Signal()

"""
    kwargs:
        - event: Event instance
"""
report_unavailable_edited = django.dispatch.Signal()
report_unavailable_deleted = django.dispatch.Signal()

"""
    kwargs:
        - report: Report instance
"""
report_busy_created = django.dispatch.Signal()
report_free_created = django.dispatch.Signal()

# currently unsed
event_set_next_occurrence = django.dispatch.Signal()  # maybe not used

"""
    kwargs:
        - event: Event instance
        - occurrences: List of datetime occurrences
"""
event_set_occurrences = django.dispatch.Signal()

"""
    kwargs:
        - room: Event room instance
"""
room_availability_changed = django.dispatch.Signal()
room_availability_free = django.dispatch.Signal()
room_availability_busy = django.dispatch.Signal()
room_availability_unavailable = django.dispatch.Signal()
room_availability_unknown = django.dispatch.Signal()
