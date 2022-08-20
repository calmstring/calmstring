from django.test import TestCase
from ..logic import signals_emiter


# logic utility method
class Test_signals_emiter(TestCase):
    def internal(self):
        self.value += 1

    def external(self):
        self.value += 4

    def test_signals_emiter_all(self):
        self.value = 0

        signals_emiter(self.internal, self.external)

        self.assertEqual(self.value, 5)

    def test_signals_emit_non(self):
        self.value = 0
        signals_emiter(self.internal, self.external, emit_signals=False)

    def test_signals_emit_internal(self):
        self.value = 0
        signals_emiter(self.internal, self.external, emit_external_signals=False)
        self.assertEqual(self.value, 1)

    def test_signals_emit_external(self):
        self.value = 0
        signals_emiter(self.internal, self.external, emit_internal_signals=False)
        self.assertEqual(self.value, 4)

    def test_when_external_not_provided(self):
        self.value = 0
        signals_emiter(self.internal, None)
        self.assertEqual(self.value, 1)

    def test_when_internal_not_provided(self):
        self.value = 0
        signals_emiter(None, self.external)
        self.assertEqual(self.value, 4)

    def test_when_internal_and_external_not_provided(self):
        self.value = 0
        signals_emiter(None, None)
        self.assertEqual(self.value, 0)
