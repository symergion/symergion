import unittest
from utils.flatten import flatten


class TestFlatten(unittest.TestCase):
    """A test suite for the flatten function,
    which is expected to take a list of lists and
    return a single flattened list containing all the elements.
    """

    def test_flatten_multiple_elements(self):
        """Tests the flatten function with a typical case where
        the input is a list of lists containing integers.
        The expected output is a single list with all the integers in order.
        """
        self.assertEqual(flatten([[1, 2], [3, 4], [5, 6]]), [1, 2, 3, 4, 5, 6])

    def test_flatten_single_elements(self):
        """Tests the flatten function with a list of lists
        where each sublist contains a single integer.
        The expected output is a single list with all the integers in order.
        """
        self.assertEqual(flatten([[1], [2], [3]]), [1, 2, 3])

    def test_flatten_empty_sublists(self):
        """Tests the flatten function with a list of empty sublists.
        The expected output is an empty list.
        """
        self.assertEqual(flatten([[], [], []]), [])

    def test_flatten_mixed_empty_and_non_empty_sublists(self):
        """Tests the flatten function with a list that
        contains both empty and non-empty sublists.
        The expected output is a single list with
        all the elements from the non-empty sublists.
        """
        self.assertEqual(flatten([[], [1, 2, 3], []]), [1, 2, 3])
