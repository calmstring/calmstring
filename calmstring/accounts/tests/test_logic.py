from django.test import TestCase
from .. import logic, commands_handlers
from ..models import VerificationCode
from ..signals import command_on_email_verification_created
from utils.exceptions import ValidationError
from django.contrib.auth import get_user_model


User = get_user_model()


class TestCreateEmailVerification(TestCase):
    def setUp(self) -> None:
        # disconnect proper command handler
        command_on_email_verification_created.disconnect(
            commands_handlers.send_verification_email
        )
        return super().setUp()

    def tearDown(self) -> None:

        command_on_email_verification_created.disconnect(self.dump_handler)

    @staticmethod
    def dump_handler(sender, **kwargs):
        return True

    def test_create_verification(self):
        command_on_email_verification_created.connect(self.dump_handler)
        logic.create_email_verification("newuser@email.com", emit_signals=False)

        vc = VerificationCode.objects.filter(email="newuser@email.com").first()

        self.assertIsNotNone(vc)

    def test_create_two_same_emais_verification(self):
        command_on_email_verification_created.connect(self.dump_handler)
        logic.create_email_verification("newuser@email.com", emit_signals=False)
        logic.create_email_verification("newuser@email.com", emit_signals=False)

        vcs = VerificationCode.objects.filter(email="newuser@email.com")

        self.assertEqual(len(vcs), 2)

    def test_create_when_command_raises_exception(self):
        def notification_send_handler(sender, **kwargs):
            raise Exception("Ups email service don't work")

        command_on_email_verification_created.connect(notification_send_handler)
        with self.assertRaises(logic.EmailCreateVerificationHanlderError):
            logic.create_email_verification(
                email="newuser@email.com", emit_signals=False
            )
        command_on_email_verification_created.disconnect(notification_send_handler)

    def test_create_when_no_command_handlers(self):
        with self.assertRaises(logic.NonEmailCreateVerificationHandlersError):
            logic.create_email_verification(
                email="newuser@email.com", emit_signals=False
            )

    def test_create_when_email_is_assigned_to_another_user(self):
        User.objects.create_user("john", "newuser@email.com", "johnpassword")
        with self.assertRaises(ValidationError):
            logic.create_email_verification(
                email="newuser@email.com", emit_signals=False
            )


class TestVerifyEmail(TestCase):
    def setUp(self) -> None:
        self.verification = None
        self.email = "newuser@email.com"

        def handler(sender, email, verification, **kwargs):
            self.verification = verification.code

        command_on_email_verification_created.connect(handler)
        logic.create_email_verification(self.email, emit_signals=False)

    def test_verify_email(self):
        verified, signature = logic.verify_email(self.email, self.verification)

        self.assertTrue(verified)

    def test_invalid_verify_email(self):
        with self.assertRaises(logic.VerificationCodeObjectNotFoundError):
            logic.verify_email(self.email, "invalid_code")


class TestRegisterUser(TestCase):
    def setUp(self) -> None:
        self.inviter = User.objects.create_user(
            "johninviter", "john@inviter.com", "johnpassword"
        )
        self.inviter.role = self.inviter.Roles.TRUSTED
        self.inviter.save()

        # create verification code and finally get signature
        self.verification = None
        self.email = "newuser@email.com"

        def handler(sender, email, verification, **kwargs):
            self.verification = verification.code

        command_on_email_verification_created.connect(handler)
        logic.create_email_verification(self.email, emit_signals=False)

        _, signature = logic.verify_email(self.email, self.verification)
        self.signature = signature

    def test_register_user(self):
        user = logic.register_user(
            inviter=self.inviter,
            email=self.email,
            password="password",
            signature=self.signature,
        )
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.is_setup, False)
        self.assertEqual(user.role, user.Roles.LIMITED)
        self.assertEqual(user.inviter, self.inviter)

    def test_invalid_register_user(self):
        with self.assertRaises(logic.InvalidSignatureError):
            logic.register_user(
                inviter=self.inviter,
                email=self.email,
                password="password",
                signature="invalid_signature",
            )

    def test_invalid_inviter_register_user(self):
        self.inviter.role = self.inviter.Roles.NORMAL
        with self.assertRaises(logic.InviterNotPermittedError):
            logic.register_user(
                inviter=self.inviter,
                email=self.email,
                password="password",
                signature=self.signature,
            )


class TestRegisterCompleteUser(TestCase):
    def setUp(self) -> None:
        # refactor this to use one function for all classes
        self.inviter = User.objects.create_user(
            "johninviter", "john@inviter.com", "johnpassword"
        )
        self.inviter.role = self.inviter.Roles.TRUSTED
        self.inviter.save()

        # create verification code and finally get signature
        self.verification = None
        self.email = "newuser@email.com"

        def handler(sender, email, verification, **kwargs):
            self.verification = verification.code

        command_on_email_verification_created.connect(handler)
        logic.create_email_verification(self.email, emit_signals=False)

        _, signature = logic.verify_email(self.email, self.verification)
        self.signature = signature

        self.user = logic.register_user(
            inviter=self.inviter,
            email=self.email,
            password="password",
            signature=self.signature,
        )

    def test_complete_register(self):
        user = logic.complete_register(
            self.user, "NewUser", "Adam Toryk", emit_signals=False
        )

        self.assertTrue(user.is_setup)
        self.assertEqual(user.username, "NewUser")
        self.assertEqual(user.full_name, "Adam Toryk")

    def test_complete_when_account_already_setup(self):
        logic.complete_register(self.user, "NewUser", "Adam Toryk", emit_signals=False)
        self.user.refresh_from_db()

        with self.assertRaises(logic.UserAlreadySetupError):
            logic.complete_register(
                self.user, "NewUser1", "Adam Toryk", emit_signals=False
            )


class TestChangeUserRole(TestCase):
    def setUp(self) -> None:
        self.editor = User.objects.create_user(
            "john", "john@inviter.com", "johnpassword"
        )
        self.editor.role = User.Roles.TRUSTED
        self.editor.save()

        self.user = User.objects.create_user("tom", "tom@tom.com", "tompassword")

    def test_change_to_role(self):
        user = logic.change_user_role(
            self.editor, self.user, User.Roles.NORMAL, emit_signals=False
        )
        self.assertEqual(user.role, User.Roles.NORMAL)

        user = logic.change_user_role(
            self.editor, self.user, User.Roles.LIMITED, emit_signals=False
        )
        self.assertEqual(user.role, User.Roles.LIMITED)

    def test_change_role_to_same_as_editor(self):
        user = logic.change_user_role(
            self.editor, self.user, User.Roles.TRUSTED, emit_signals=False
        )
        self.assertEqual(user.role, User.Roles.TRUSTED)

    def test_invalid_change_role_to_higher_than_editor(self):
        with self.assertRaises(ValidationError):
            logic.change_user_role(
                self.editor, self.user, User.Roles.ADMINISTRATIVE, emit_signals=False
            )
