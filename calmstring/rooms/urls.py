from django.urls import path
from rest_framework import routers

from .views import RoomsViewSet

router = routers.DefaultRouter()

router.register("", RoomsViewSet, basename="RoomsViewSet")


urlpatterns = [] + router.urls
