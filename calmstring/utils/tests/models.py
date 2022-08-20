from django.db import models
from ..models import SoftDeleteModel, UUIDModel


class CustomSoftDeleteModel(SoftDeleteModel):
    name = models.CharField(max_length=20)


class KeyUuidModel(UUIDModel):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class ModelWithKey(models.Model):
    key = models.ForeignKey(KeyUuidModel, on_delete=models.CASCADE)
