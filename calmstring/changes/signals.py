import django.dispatch

"""
    Signal called by an reverted() when we are reverting version of some obejct
    
    kwargs:
        - reverted      : object we are reverting from
        - to            : new reverted object
        - content_object: generated content_object from new reverted version (not saved)
"""
change_reverted = django.dispatch.Signal()

"""
    Signal called by an object that wanna signalize change
    
    kwargs:
        - type               : string that will allow to identify change type
        - content_object     : django model instance
        - changes (optional) : dict of chanages or null. If null whole object will be serialized
"""
change_done = django.dispatch.Signal()