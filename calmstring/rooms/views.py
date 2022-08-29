from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from . import logic, serializers, models
from utils.api.views import LogicAPIView

from accounts.permissions import IsLimitedUser, IsAdministrativeUser

# Create your views here.
class RoomsViewSet(
    LogicAPIView,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.RoomSerializer
    lookup_field = "uuid"
    queryset = models.Room.objects.all()

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAdministrativeUser]
        else:
            permission_classes = [IsLimitedUser]

        return [permission() for permission in permission_classes]

    def create(self, *args, **kwargs):
        super().create(*args, **kwargs)

        name = self.validated_data["name"]
        description = self.validated_data["description"]

        room = logic.create_room(name, description)

        data = self.get_serializer_class()(room).data

        return Response(data, status=status.HTTP_201_CREATED)
