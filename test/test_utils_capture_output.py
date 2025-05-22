import unittest
from utils import capture_output


class TestCaptureOutput(unittest.TestCase):
    """A test case class to verify the functionality of the `capture_output` utility function.
    """

    def test_capture_output(self):
        """Tests that the `capture_output` function correctly
        captures the standard output of a given function.
        This method defines a simple function that prints "Hello, World!" and then
        uses `capture_output` to capture the output of this function.
        It asserts that the captured output matches the expected string".
        """
        def test_function():
            """A helper function that prints "Hello, World!" to the standard output.
            """
            print("Hello, World!")

        output = capture_output(test_function)

        self.assertEqual("Hello, World!", output)
