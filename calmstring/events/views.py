from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, generics, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action

from .serializers import (
    EventSerializer,
    OccupyRoomSerializer,
    OccupyRoomEditSerializer,
    OccupyRoomFreeSerializer,
    ReportSerializer,
    EventUnavailableSerializer,
    EventUnavailableEditSerializer,
)
from .filters import EventListFilter
from .permissions import IsEventAuthor

from accounts.permissions import (
    IsLimitedUser,
    IsCompetitiveUser,
    IsTrustedUser,
    IsNormalUser,
)
from utils.api.permissions import IsReadyOnly
from utils.api.views import LogicAPIView

from .models import Event
from . import logic, exceptions

import logging

logger = logging.getLogger(__name__)


class EventsListAPIView(generics.ListAPIView):

    queryset = Event.objects.all().existing()
    serializer_class = EventSerializer
    filterset_class = EventListFilter
    permission_classes = [IsLimitedUser]

    def list(self, request):
        queryset = self.get_queryset()
        serializers = self.get_serializer_class()(queryset, many=True)
        return Response(serializers.data)


class EventLogicViewBase:
    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsNormalUser]
        else:
            permission_classes = [IsEventAuthor | IsCompetitiveUser]

        return [permission() for permission in permission_classes]


class OccupyRoomViewset(
    LogicAPIView,
    EventLogicViewBase,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OccupyRoomSerializer
    lookup_field = "uuid"
    queryset = (
        Event.objects.all().existing().filter(availability=Event.Availabilities.BUSY)
    )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)

        room = self.validated_data["room"]
        author = request.user
        start_date = self.validated_data["start_date"]

        end_date = self.validated_data.get("end_date", None)
        name = self.validated_data.get("name", None)
        description = self.validated_data.get("description", None)
        try:
            event = logic.occupy_room(
                room, author, start_date, end_date, name, description
            )
        except exceptions.NotEndedEventExists:
            return Response(
                {self.DETAIL_KEY: _("You've got not ended event in this room")},
            )
        except exceptions.OverlapedEventExists:
            return Response(
                {self.DETAIL_KEY: _("Your event overlaps with your another event")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = self.get_serializer_class()(event).data
        return Response(
            data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, *args, **kwargs):
        return Response(
            {self.DETAIL_KEY: _("Method not supported user PATCH instead")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        self.serializer_class = OccupyRoomEditSerializer

        super().partial_update(request, *args, **kwargs)

        author = request.user

        try:
            event = logic.edit_occupy_room(self.object, author, **self.validated_data)
        except exceptions.ValidationError as e:
            return Response(
                {self.DETAIL_KEY: e},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exceptions.OverlapedEventExists:
            return Response(
                {self.DETAIL_KEY: _("Your event overlaps with your another event")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = EventSerializer(event).data
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        user = request.user

        try:
            logic.delete_occupy_room(event, user)
        except exceptions.ValidationError as e:
            return Response(
                {self.DETAIL_KEY: e},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {self.DETAIL_KEY: _("Occupation successfully deleted")},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=True, methods=["post"])
    def free(self, request, *args, **kwargs):
        self.serializer_class = OccupyRoomFreeSerializer
        super().update(request, *args, **kwargs)

        author = request.user
        room = self.object.room
        end_date = self.validated_data["end_date"]

        try:
            event = logic.free_room(room, author, end_date)
        except exceptions.NotEndedEventDoesNotExist:
            return Response(
                {self.DETAIL_KEY: _("You've got not ended event in this room")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = EventSerializer(event).data
        return Response(data, status=status.HTTP_200_OK)


class EventUnavailableRoomViewset(
    LogicAPIView,
    EventLogicViewBase,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = EventUnavailableSerializer
    lookup_field = "uuid"
    queryset = Event.objects.existing().filter(
        availability=Event.Availabilities.UNAVAILABLE
    )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)

        room = self.validated_data["room"]
        user = request.user
        start_date = self.validated_data["start_date"]
        end_date = self.validated_data["end_date"]
        name = self.validated_data.get("name", None)
        description = self.validated_data.get("description", None)
        recurrences = self.validated_data.get("recurrences", None)

        object = logic.report_unavailable(
            room, user, start_date, end_date, name, description, recurrences
        )

        data = EventSerializer(object).data
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, *args, **kwargs):
        return Response(
            {self.DETAIL_KEY: _("Method not supported user PATCH instead")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        self.serializer_class = EventUnavailableEditSerializer
        super().partial_update(request, *args, **kwargs)

        user = request.user

        event = logic.edit_report_unavailable_event(
            self.object, user, **self.validated_data
        )

        data = EventSerializer(event).data

        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        user = request.user

        logic.delete_report_unavailable_event(event, user)

        return Response(
            {self.DETAIL_KEY: _("Event successfully deleted")},
            status=status.HTTP_204_NO_CONTENT,
        )
