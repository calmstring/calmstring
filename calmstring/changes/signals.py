import django.dispatch


CHANGE_REVERTED = django.dispatch.Signal()
CHANGE_DONE = django.dispatch.Signal()