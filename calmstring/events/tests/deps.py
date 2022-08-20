from rooms.models import Room


def create_room(name, description=""):
    return Room.objects.create(name=name, description=description)