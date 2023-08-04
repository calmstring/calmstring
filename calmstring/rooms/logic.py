from .models import Room
from . import signals as room_signals
from utils.logic import signals_emiter


def create_room(name, description, **kwargs):
    room = Room.objects.create(name=name, description=description)

    def internal_signals():
        room_signals.room_created.send_robust("create_room", room=room)

    signals_emiter(internal_signals, None, **kwargs)

    return room
