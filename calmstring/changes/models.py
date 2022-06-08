import json
import struct
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers


from utils.models import UUIDModel,TimestampsModel

class ChangeTypeError(Exception):
    pass

class Change(UUIDModel,TimestampsModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="Change author",null=True,on_delete=models.SET_NULL)
    name = models.CharField("Change name",max_length=200,null=True,blank=True,default="")
    type = models.SlugField()
    changes = models.JSONField(default=dict)
    parent = models.ForeignKey('self',null=True,blank=True,on_delete=models.SET_NULL)
    
    content_type = models.ForeignKey(ContentType,verbose_name="Object content type",on_delete=models.CASCADE)
    content_id = models.PositiveIntegerField(verbose_name="Object id")
    content_object = GenericForeignKey('content_type','content_id')
    
    def save(self,*args, **kwargs):
        # Monipulate over save change operation
        
        changes = None
        if 'changes' in kwargs.keys():
            changes = kwargs['changes']
            
        content_object = kwargs['content_object']
        
        # if no changes varible provided then serialize whole object
        if not changes or not isinstance(changes,dict):
            try:
                data = serializers.serialize(
                    'json',
                    [content_object, ],
                    use_natural_foreign_keys=True,
                    use_natural_primary_keys=True
                    )
                struct = json.loads(data)
                changes = struct[0]
                
            except serializers.SerializationError:
                raise serializers.SerializationError(f'Can\'t serialize content_object: {content_object}')
        
        self.changes = changes
        
        # set type to model if no type provided
        if 'type' not in kwargs.keys():
            self.type = content_object._meta.app_label
        
        return super().save(*args, **kwargs)
    
    def reverted(self,to):
        """Get reverted object from current state to state provided in args

        Args:
            to (Change): Change object
        """
        
        if to.type != self.type and to.pk != self.pk:
            raise ChangeTypeError()
        
        for field_name,value in to.changes.items():
            setattr(self.content_object,field_name,value)
            
        return self.content_object