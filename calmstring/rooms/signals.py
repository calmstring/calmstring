import django.dispatch

"""
    kwargs:
    - room
"""
room_created = django.dispatch.Signal()
room_edited = django.dispatch.Signal()
room_deleted = django.dispatch.Signal()