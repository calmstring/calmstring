from django_filters import rest_framework as filters
from .models import Event


class EventListFilter(filters.FilterSet):
    min_start_date = filters.DateTimeFilter(field_name="start_date", lookup_expr="gte")
    max_end_date = filters.DateTimeFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = ["start_date", "end_date", "is_recurring", "room"]
