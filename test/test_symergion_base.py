import unittest

from symergion.base import SymErgion
from symerg.base import SymErg


class TestSymErgion(unittest.TestCase):
    """This class contains unit tests for the SymErgion class.
    """

    def setUp(self):
        """Sets up the test environment before each test method is executed.
        Initializes a SymErgionSub instance and a SymErgSub instance.
        """
        self.checkpoint = {
            "name_or_path": "/test/model",
            "trait": "coding"
        }

        class SymErgionSub(SymErgion):
            """Implements symergion deriving from SymErgion abstract class.
            """
            def update(self, message):
                """Stub implementation"""
            def instantiate_symerg(self, checkpoint):
                """Stub implementation"""
            def instantiate_ergon(self, name):
                """Stub implementation"""
            def decomission_symerg(self, checkpoint):
                """Stub implementation"""
            def decomission_ergon(self, ergon):
                """Stub implementation"""
            def _notify(self, message, symergs):
                """Stub implementation"""
        self.symergion = SymErgionSub()

        class SymErgSub(SymErg):
            """Implements symerg deriving from SymErg abstract class.
            """
            def update(self, message):
                """Stub implementation"""
            def _notify(self, message):
                """Stub implementation"""
        self.symerg = SymErgSub(self.checkpoint, 1, 10, 64)

    def test_init(self):
        """Tests the initialization of the SymErgionSub instance.
        Verifies that:
            - the instance is an instance of SymErgion,
            - the symergs and ergons lists are initialized correctly.
        """
        self.assertIsInstance(self.symergion, SymErgion)
        self.assertIsInstance(self.symergion._symergs, list)
        self.assertEqual(len(self.symergion._symergs), 0)
        self.assertIsInstance(self.symergion._ergons, list)
        self.assertEqual(len(self.symergion._ergons), 0)

    def test_attach_symerg(self):
        """Tests the attach_symerg method.
        Attaches a SymErgSub instance to the SymErgionSub instance,
        verifies that the attached SymErg instance is correctly added to the symergs list.
        """
        self.symergion.attach_symerg(self.symerg)
        attached_name_or_path = self.symergion.symergs[-1].name_or_path

        self.assertIsInstance(self.symergion.symergs[-1], SymErg)
        self.assertEqual(attached_name_or_path, self.checkpoint.get("name_or_path"))

    def test_detach_symerg(self):
        """Tests the detach_symerg method.
        Detaches a SymErgSub instance from the SymErgionSub instance,
        verifies that the symergs list is empty after detachment.
        """
        self.symergion.detach_symerg(self.symerg)

        self.assertEqual(len(self.symergion.symergs), 0)

    def test_symergs(self):
        """Tests the symergs property.
        Verifies that the symergs property returns the same list as _symergs.
        """
        self.assertListEqual(self.symergion.symergs, self.symergion._symergs)

    def test_ergons(self):
        """Tests the ergons property.
        Verifies that the ergons property returns the list of ergons
        from all attached SymErg instances.
        """
        ergons = [ergon for symerg in self.symergion.symergs for ergon in symerg.ergons]

        self.assertListEqual(self.symergion.ergons, ergons)
