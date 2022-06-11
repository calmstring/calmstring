import json
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.dispatch import receiver


from utils.models import UUIDModel,TimestampsModel

from .signals import change_reverted,change_done

class ChangeTypeError(Exception):
    pass

class SameChangeError(Exception):
    pass
class DifferentContentObjectError(Exception):
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
    object_uuid = models.UUIDField()
    
    #{reverted_from:None}
    metadata = models.JSONField(default=dict({'reverted_from':None,'hidden':False}))
    
    @classmethod
    def on_change(cls,omit_same=True,*args, **kwargs):
        """on_change adds new change object to referenced content_object

        Args:
            author (<User>,required): Change author
            content_object (<Model object>,required): Reference to an object to which changes belong to.
            changes (dict,optional): Changes that will be saved in Change object. Default to dict of content_object
            type (str,optional): Slug name to identify changes. Default to content_object._meta.app_label
            uuid (uuid|str,optional): uuid that should belongs to content_object. Default to content_object.uuid
            name (str,optional): name of the change
            omit_same (bool, optional): Skips creating objects where no changes was done. Defaults to True.
        Raises:
            serializers.SerializationError: When changes are not serializable

        Returns:
            (Change|None): Change object or None if Change not created (couse omit_same)
        """
        # Manipulate over save change operation
        author = kwargs['author']
        
        name = ''
        if 'name' in kwargs.keys():
            name = kwargs['name']
        
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
                    use_natural_primary_keys=True
                    )
                struct = json.loads(data)
                changes = struct[0]['fields']
                
            except serializers.SerializationError:
                raise serializers.SerializationError(f'Can\'t serialize content_object: {content_object}')
        
        
        # set type to model if no type provided\
        type_ = content_object._meta.app_label
        if 'type' in kwargs.keys():
            type_ = kwargs['type'] 

        object_uuid = None
        if 'uuid' in kwargs.keys():
            object_uuid = kwargs['uuid']
        else:
            object_uuid = content_object.uuid
            
        # get parent
        parent = cls.objects.filter(object_uuid=object_uuid).order_by('-id').first()
        
        if parent and omit_same:
            if parent.changes == changes:
                return

        return cls.objects.create(
            author=author,
            name=name,
            changes=changes,
            content_object=content_object,
            type=type_,
            object_uuid=object_uuid,
            parent=parent
            )
    
    @classmethod
    def latest_change(cls,object_uuid):
        """Get latest change for gived object_uuid"""
        return cls.objects.filter(object_uuid=object_uuid).order_by('-id').first()
    @classmethod
    def latest_from(cls,change_obj,**kwargs):
        
        type_ = change_obj.type
        name = change_obj.name
        author = change_obj.author
        
        if 'type' in kwargs.keys():
            type_ = kwargs['type_']
        
        if 'name' in kwargs.keys():
            name = kwargs['name']
            
        if 'author' in kwargs.keys():
            author = kwargs['author']
            
        metadata = {
            'reverted_from':change_obj.id,
            'reverted_from_uuid':str(change_obj.uuid),
            'hidden':False,
            }
        
        return cls.objects.create(
            content_object=change_obj.content_object,
            changes=change_obj.changes,
            object_uuid=str(change_obj.object_uuid),
            parent=cls.latest_change(change_obj.object_uuid),
            type=type_,
            name=name,
            author=author,
            metadata=metadata
            
        )
    @classmethod
    def reverted(cls,to,**kwargs):
        """Get reverted content_object of from given 

        Args:
            to (Change,required): Change we want to revert to
            name (str,optional): Name provided for new reverted change
            type (str,optional): Type provided for new reverted change

        Raises:
            SameChangeError: When to is self object

        Returns:
            tuple: (reverted_changes,content_object)
        """
        latest_change = cls.latest_change(to.object_uuid)
        
        if to.pk == latest_change.pk:
            return (latest_change,content_object)
        
        reverted_changes = cls.latest_from(to)
        
        
        # generated new reverted version of content_object
        content_object = reverted_changes.content_object
        for field_name,value in to.changes.items(**kwargs):
            
            # get django db.models field
            field = content_object._meta.get_field(field_name)
            
            if isinstance(field,models.ManyToManyField):
                getattr(content_object,field_name).set(value)
            else:
                setattr(content_object,field_name,value)
                
        change_reverted.send(
            sender='reverted',
            reverted=to,
            to=latest_change,
            content_object=content_object,
            )
        
        return (latest_change,content_object)
    
@receiver(change_done)
def proccess_change(sender,**kwargs):
    return Change.on_change(**kwargs)
