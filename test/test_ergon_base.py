import unittest
from ergon.base import Ergon


class TestErgon(unittest.TestCase):
    """This class contains unit tests for the Ergon class.
    """

    def setUp(self):
        """Sets up the test environment by creating an instance of Ergon implementation.
        """
        class ErgonSub(Ergon):
            """Implements ergon deriving from Ergon abstract class
            """
            def update(self, message):
                """Stub implementation"""

        self.ergon = ErgonSub("abcd")

    def test_init(self):
        """Tests the initialization of the Ergon class.
        Ensures that the instance is of type Ergon and that the name attribute is set correctly.
        """
        self.assertIsInstance(self.ergon, Ergon)
        self.assertEqual(self.ergon.name, "abcd")
