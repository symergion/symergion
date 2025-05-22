import unittest
from unittest.mock import Mock

from handler.base import Handler


class TestHandler(unittest.TestCase):
    """This class tests the basic functionality of the Handler class.
    """
    def setUp(self):
        """Set up the test environment.
        Initializes a mock Symergion object,
        instantiates the Handler class with this mock.
        """
        class HandlerSub(Handler):
            """Stub implementation"""
            def dispatch(self, event):
                """Stub implementation"""
            def sync_state(self):
                """Stub implementation"""

        self.symergion = Mock()
        self.handler = HandlerSub(self.symergion)

    def test_init(self):
        """Test the initialization of the Handler class.
        """
        self.assertEqual(self.handler.symergion, self.symergion)
