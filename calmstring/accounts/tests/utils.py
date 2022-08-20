from .. import commands_handlers
from ..signals import command_on_email_verification_created


class email_verification_created_handler:
    """Used to manage signal connection of send_verification_email"""

    @classmethod
    def connect(cls):
        command_on_email_verification_created.connect(
            commands_handlers.send_verification_email
        )

    @classmethod
    def disconnect(cls):
        command_on_email_verification_created.disconnect(
            commands_handlers.send_verification_email
        )
