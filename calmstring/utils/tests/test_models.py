from django.test import TestCase
from .models import CustomSoftDeleteModel


class TestModelDefinition(TestCase):
    def setUp(self):
        self.obj = CustomSoftDeleteModel.objects.create(name="test")

    def test_model_definition(self):
        self.assertEqual(self.obj.is_deleted, False)
        self.obj.soft_delete()
        self.assertEqual(self.obj.is_deleted, True)

    def test_model_restore(self):
        self.obj.soft_delete()

        self.obj.restore()
        self.assertEqual(self.obj.is_deleted, False)

    def test_model_restore_no_save(self):
        self.obj.soft_delete()

        self.obj.restore(save=False)
        self.assertEqual(self.obj.is_deleted, False)
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.is_deleted, True)


class TestSoftDeleteQuerySet(TestCase):
    def setUp(self):
        for i in range(10):
            obj = CustomSoftDeleteModel.objects.create(name=f"test{i}")
            setattr(self, f"obj{i}", obj)

    def test_existing(self):
        existing_count = lambda: CustomSoftDeleteModel.objects.existing().count()
        self.assertEqual(existing_count(), 10)

        self.obj1.soft_delete()
        self.assertEqual(existing_count(), 9)

    def test_soft_deleted(self):
        soft_deleted_count = (
            lambda: CustomSoftDeleteModel.objects.soft_deleted().count()
        )

        self.assertEqual(soft_deleted_count(), 0)

        self.obj1.soft_delete()
        self.obj2.soft_delete()
        self.obj3.soft_delete()

        self.assertEqual(soft_deleted_count(), 3)

    def test_filtering(self):

        existing_obj1 = (
            CustomSoftDeleteModel.objects.existing().filter(name="test1").first()
        )
        self.assertEqual(existing_obj1, self.obj1)

        self.obj1.soft_delete()

        soft_deleted_obj1 = (
            CustomSoftDeleteModel.objects.soft_deleted().filter(name="test1").first()
        )

        self.assertEqual(soft_deleted_obj1, self.obj1)
