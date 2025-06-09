import unittest

from utils import capture_output
from utils import in_memory_cache


class TestLruCache(unittest.TestCase):
    """A test case for the LRU (Least Recently Used) Cache implementation.
    This class tests the functionality of the `in_memory_cache` decorator by ensuring that
    cached results are correctly returned without re-executing the function when
    the same arguments are provided again.
    """

    def setUp(self):
        """Set up the test environment.
        Creates an instance of a class with a method decorated with `in_memory_cache`.
        """
        class Simple():
            """A class with a method decorated with `in_memory_cache`.
            The method simulates a simple addition operation and
            prints a message indicating whether it is running.
            """
            def __init__(self):
                self._cache_size = 1

            @in_memory_cache("_cache_size")
            def add(self, a, b):
                """A simple addition method with caching enabled.

                Args:
                    a (int): The first number to add.
                    b (int): The second number to add.

                Returns:
                    int: The sum of `a` and `b`.

                Prints:
                    "add is running" when the method is
                    executed for the first time
                    with the given arguments.
                """
                print("add is running")
                return a + b

        self.simple = Simple()

    def test_in_memory_cache(self):
        """Test the LRU cache functionality.
        Verifies that the cached result is returned on subsequent calls
        with the same arguments, and
        that the function body is not re-executed.
        """
        # Capture the output and result of the first run
        first_run_output = capture_output(self.simple.add, 1, 2)

        # Assert that the output indicates the function was running
        self.assertEqual("add is running", first_run_output)

        # Capture the output and result of the second run
        second_run_output = capture_output(self.simple.add, 1, 2)

        # Assert that the output does not indicate the function was running again
        self.assertNotEqual("add is running", second_run_output)

        # Assert that the cached result is correct
        self.assertEqual(self.simple.add(1, 2), 3)
