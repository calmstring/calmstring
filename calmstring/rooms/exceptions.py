class NotEndedEventExists(Exception):
    pass

class NotEndedEventDoesNotExist(Exception):
    pass

class MultipleNotEndedEventsExists(Exception):
    pass

class OverlapedEventExists(Exception):
    pass

class ValidationError(Exception):
    pass