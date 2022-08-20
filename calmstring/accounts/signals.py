import django.dispatch


"""
    kwargs:
    - email: str
    - verification: VerificationCode
"""
command_on_email_verification_created = (
    django.dispatch.Signal()
)  # command type signal (needs just one receiver)
on_email_verification_created = django.dispatch.Signal()
on_email_verified = django.dispatch.Signal()

"""
    Users base signals
    kwargs:
        - user: User    
"""
user_created = django.dispatch.Signal()
user_edited = django.dispatch.Signal()
user_deleted = django.dispatch.Signal()

"""
Called when user successfully completed registration
    kwargs:
        - user: User
"""
user_registered = django.dispatch.Signal()

""" User role signal
    kwargs:
        - user: User
        - last_role: User.Roles
        - new_role: User.Roles
"""
user_role_changed = django.dispatch.Signal()
