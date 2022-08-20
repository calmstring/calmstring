from django.dispatch import receiver
from . import signals as accounts_signals


@receiver(accounts_signals.user_created)
def create_allauth_email_address(sender, user, **kwargs):
    from allauth.account.models import EmailAddress

    email = EmailAddress(user=user, email=user.email, primary=True, verified=True)
    email.save()
