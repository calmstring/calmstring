import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calmstring.settings")

application = get_wsgi_application()

# load rooms and fixtures

floors = ["2", "3", "4", "5"]
rooms = ["19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]

from rooms.logic import create_room

for floor in floors:
    for room in rooms:
        name = f"{floor}.{room}"
        description = f"{name} description"
        create_room(name=name, description=description)
