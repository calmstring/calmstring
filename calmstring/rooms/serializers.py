from rest_framework import serializers
from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["availability"] = instance.availability

        data["events_room_uuid"] = instance.events_room_uuid
        return data
