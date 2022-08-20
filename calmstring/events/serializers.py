from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .validators import validate_dates, validate_recurrence
from . import conf, exceptions

from .models import Event, EventRoom, Report


from utils.api.serializers import UUIDRelatedField

User = get_user_model()


class RoomField(UUIDRelatedField):
    queryset = EventRoom.objects.all()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, uuid_field="uuid", **kwargs)


class AuthorField(UUIDRelatedField):
    queryset = User.objects.all()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, uuid_field="uuid", **kwargs)


class EventSerializer(serializers.ModelSerializer):

    room = RoomField()
    author = AuthorField()

    class Meta:
        model = Event
        exclude = ["id"]


class OccupyRoomSerializer(serializers.ModelSerializer):
    room = RoomField()

    class Meta:
        model = Event
        fields = ["start_date", "end_date", "name", "description", "room"]

    def validate(self, data):

        start_date = data.get("start_date") or self.instance.start_date
        end_date = None
        try:
            end_date = data.get("end_date") or self.instance.end_date
        except:
            pass

        if not end_date:
            return data

        try:
            validate_dates(start_date, end_date, max_duration=conf.MAX_BUSY_DURATION)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e)

        return data


class OccupyRoomEditSerializer(OccupyRoomSerializer):
    class Meta:
        model = Event
        fields = [
            "start_date",
            "end_date",
            "name",
            "description",
        ]


class OccupyRoomFreeSerializer(OccupyRoomEditSerializer):
    class Meta:
        model = Event
        fields = [
            "end_date",
        ]


class EventUnavailableSerializer(serializers.ModelSerializer):
    room = RoomField()

    class Meta:
        model = Event
        fields = [
            "room",
            "start_date",
            "end_date",
            "name",
            "description",
            "recurrences",
        ]

    def validate(self, data):

        start_date = data.get("start_date") or self.instance.start_date
        end_date = None
        try:
            end_date = data.get("end_date") or self.instance.end_date
        except:
            pass
        recurrences = data.get("recurrences") or self.instance.recurrences

        try:
            validate_dates(start_date, end_date)
            validate_recurrence(start_date, end_date, recurrences)

        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e)

        return data


class EventUnavailableEditSerializer(EventUnavailableSerializer):
    class Meta:
        model = Event
        fields = [
            "start_date",
            "end_date",
            "name",
            "description",
            "recurrences",
        ]


class ReportSerializer(serializers.ModelSerializer):
    room = RoomField()
    author = AuthorField()

    class Meta:
        model = Report
        exclude = ["id"]
