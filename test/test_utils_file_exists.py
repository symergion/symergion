import unittest
import os

from utils import file_exists


class TestFileExists(unittest.TestCase):
    """TestFileExists contains unit tests to verify the `file_exists` utility function.
    """
    def setUp(self):
        """Set up the test environment by creating a temporary file before each test method is run.
        """
        self.file_path = "test_file.txt"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("Test file content")

    def tearDown(self):
        """Clean up the test environment.
        Removes the temporary file after each test method is run.
        """
        os.remove(self.file_path)

    def test_file_exists(self):
        """Test that the `file_exists` function returns True when the specified file exists.
        """
        self.assertTrue(file_exists(self.file_path))

    def test_file_does_not_exist(self):
        """Test that the `file_exists` function returns False
        when the specified file does not exist.
        """
        self.assertFalse(file_exists("nonexistent_file.txt"))
