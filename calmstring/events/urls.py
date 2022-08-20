from django.urls import path, include
from rest_framework import routers

from .views import EventsListAPIView, OccupyRoomViewset, EventUnavailableRoomViewset

router = routers.DefaultRouter()
router.register(r"occupy", OccupyRoomViewset, basename="OccupyRoomViewset")
router.register(
    r"unavailable",
    EventUnavailableRoomViewset,
    basename="EventUnavailableRoomViewset",
)


urlpatterns = [
    path("", EventsListAPIView.as_view(), name="EventsListAPIView"),
    # "reports/" POST
] + router.urls
