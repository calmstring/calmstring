from django.dispatch import receiver
from .signals import command_on_email_verification_created
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.template.loader import render_to_string
from . import conf


@receiver(command_on_email_verification_created)
def send_verification_email(sender, email, verification, **kwargs):
    """
    Sends verification email to user
    """
    print("Code: ", verification.code)
    return True

    html_message = render_to_string(
        "accounts/verification_email.html",
        {
            "code": verification.code,
            "expiration_minutes": int(conf.ACCOUNTS_CODE_EXPIRATION_TIME / 60),
        },
    )

    send_mail(
        _("Verify your email address"),
        "Thanks for starting the new Calmstring account creation process. We want to make sure it's really you. Please enter the following verification code when prompted. If you don’t want to create an account, you can ignore this message.\n\nVerification code:\n{}\n(This code is valid for {} minutes)\n\nThanks,\nThe Calmstring team".format(
            verification.code, int(conf.ACCOUNTS_CODE_EXPIRATION_TIME / 60)
        ),
        None,
        [email],
        fail_silently=False,
        html_message=html_message,
    )
