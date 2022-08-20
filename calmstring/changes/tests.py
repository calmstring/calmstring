from django.test import TestCase
from django.conf import settings

from .models import Change, DifferentContentObjectError
from .signals import change_done
from django.contrib.auth import get_user_model

User = get_user_model()


class TestOnChangeMethod(TestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user("user", "user@user.com", "user")
        self.content_object = User.objects.create_user("adam", "adam@adam.com", "adam")
        return super().setUp()

    def test_change_done_one_property(self):

        self.content_object.full_name = "origin"
        self.content_object.save()

        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_CREATE_FIRSTNAME",
            changes={"USER_FIRSTNAME": self.content_object.full_name},
        )

        self.assertEqual(Change.objects.all().count(), 1)

        our_change = Change.objects.all().first()

        self.assertEqual(
            our_change.changes, {"USER_FIRSTNAME": self.content_object.full_name}
        )

    def test_change_done_whole_object(self):

        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_CREATED",
            changes=self.content_object,
        )

        self.assertEqual(Change.objects.all().count(), 1)

        our_change = Change.objects.all().first()

    def test_add_few_changes(self):
        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_CREATED",
            changes=self.content_object,
        )

        self.content_object.full_name = "origin"
        self.content_object.save()
        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )

        self.content_object.full_name = "master"
        self.content_object.save()
        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )

        our_changes = Change.objects.all()

        self.assertEqual(our_changes.count(), 3)

    def test_omit_same(self):
        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_CREATED",
            changes=self.content_object,
        )

        # when someone in API calls PUT/PATCH and no changes was provided
        change_done.send(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )
        with_omit_count = Change.objects.all().count()
        self.assertEqual(with_omit_count, 1)

        # disable omiting same records
        change_done.send(
            omit_same=False,
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )

        without_omit_count = Change.objects.all().count()
        self.assertEqual(without_omit_count, 2)


class TestReverted(TestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user("user", "user@user.com", "user")
        self.content_object = User.objects.create_user("adam", "adam@adam.com", "adam")
        self.content_object1 = User.objects.create_user(
            "adam1", "adam1@adam.com", "adam1"
        )
        return super().setUp()

    def test_revert_changes(self):
        # add few changes
        _, change0 = change_done.send_robust(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_CREATED",
            changes=self.content_object,
        )[0]

        self.content_object.full_name = "origin"
        self.content_object.save()
        _, change1 = change_done.send_robust(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )[0]

        self.content_object.full_name = "master"
        self.content_object.save()
        _, change2 = change_done.send_robust(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )[0]

        self.assertEqual(self.content_object.full_name, "master")

        _, reverted_content_object = Change.reverted(to=change1)

        self.assertEqual(reverted_content_object.full_name, "origin")

    def test_ManyToManyField_changes(self):
        _, change0 = change_done.send_robust(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_CREATED",
            changes=self.content_object,
        )[0]

        # create group
        from django.contrib.auth.models import Group

        group = Group.objects.create(name="groupname")

        self.content_object.groups.add(group)

        _, change1 = change_done.send_robust(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )[0]

        group2 = Group.objects.create(name="groupname2")
        # group1 = Group.objects.get(name='groupname')

        self.content_object.groups.add(group2)

        _, change2 = change_done.send_robust(
            sender=self.__class__,
            author=self.author,
            content_object=self.content_object,
            type="USER_EDITED",
            changes=self.content_object,
        )[0]

        self.assertEqual(self.content_object.groups.all().count(), 2)

        _, reverted_content_object = Change.reverted(to=change1)

        self.assertEqual(reverted_content_object.groups.all().count(), 1)
