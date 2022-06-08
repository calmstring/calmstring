
from django.db import models
import uuid

from django.utils.deconstruct import deconstructible
import os
import re

class UUIDModel(models.Model):
    """Abstract model that provides additional fields to model: 
            uuid: (models.UUIDField)
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    class Meta:
        abstract = True
        
class TimestampsModel(models.Model):
    """Abstract model that provides specific for timestamps additional fields:
            created_at: DateTimeField - set to now when creating object
            updated_at: DateTimeField - set to now on every update
    """
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True

@deconstructible
class PathAndRename(object):

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)

    '''
    class from :
        https://stackoverflow.com/questions/25767787/django-cannot-create-migrations-for-imagefield-with-dynamic-upload-to-value
        https://code.djangoproject.com/ticket/22999
    '''