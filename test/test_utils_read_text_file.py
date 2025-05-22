import unittest
from os import remove
from utils import read_text_file


class TestReadTextFile(unittest.TestCase):
    """A test case class for the read_text_file function.
    This class includes tests to verify the functionality of reading text files.
    """
    def setUp(self):
        """Set up the test environment by creating a temporary text file.
        The file contains the string "Hello, World!".
        """
        self.file_path = "test.txt"
        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write("Hello, World!")

    def tearDown(self):
        """Clean up the test environment by removing the temporary text file.
        """
        remove(self.file_path)

    def test_read_text_file(self):
        """Test the read_text_file function with an existing file.
        Asserts that the content of the file is correctly read and matches "Hello, World!".
        """
        content = read_text_file(self.file_path)
        self.assertEqual(content, "Hello, World!")

    def test_read_nonexistent_file(self):
        """Test the read_text_file function with a non-existent file.
        Asserts that a FileNotFoundError is raised when attempting to read a non-existent file.
        """
        with self.assertRaises(FileNotFoundError):
            read_text_file("nonexistent.txt")
