from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status
from utils.for_tests import TestCaseWithUsers


class TestRoomsViewSet(TestCaseWithUsers):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.room_name = "Room 1"
        self.room_description = "Room 1 description"

    def test_create_room_with_permission(self):
        self.client.force_authenticate(user=self.administrative_user)
        response = self.client.post(
            reverse("RoomsViewSet-list"),
            {"name": self.room_name, "description": self.room_description},
        )
        self.assertTrue(status.is_success(response.status_code))
