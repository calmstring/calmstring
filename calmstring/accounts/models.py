from django.db import models

from django.contrib.auth.models import AbstractUser

from utils.models import UUIDModel
# Create your models here.
class User(UUIDModel,AbstractUser):
    pass