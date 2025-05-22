import os
import shutil
import unittest

from utils import verified_file_name


class TestVerifiedFileName(unittest.TestCase):
    """Test case for the `verified_file_name` function.
    This class contains unit tests to verify the behavior of the `verified_file_name`
    function under various conditions, including file existence and directory handling.
    """

    def setUp(self):
        """Set up the test environment before each test method.
        Creates a temporary directory and a test file within it.
        """
        self.dir = "/test_dir"
        os.mkdir(self.dir)
        self.file_name = "test_source_file"
        with open(f"{self.dir}/{self.file_name}", "w", encoding="utf-8") as f:
            f.write("test file content")
        self.new_file_name = "new_file_name"

    def tearDown(self):
        """Clean up the test environment after each test method.
        Removes the temporary directory and all its contents.
        """
        shutil.rmtree(self.dir)

    def test_verified_file_name_is_new(self):
        """Test the `verified_file_name` function when the file is new.
        Verifies that the function returns the provided file name if it is marked as new
        and does not exist in the directory.
        """
        verified_new_file_name = verified_file_name(self.dir, self.new_file_name, is_new=True)
        self.assertEqual(verified_new_file_name, self.new_file_name)

    def test_verified_file_name_is_not_new(self):
        """Test the `verified_file_name` function when the file is not new.
        Verifies that the function returns the provided file name if it is not marked as new
        and exists in the directory.
        """
        self.assertEqual(verified_file_name(self.dir, self.file_name), self.file_name)

    def test_verified_file_name_is_not_new_and_no_file(self):
        """Test the `verified_file_name` function when the file is not new but does not exist.
        Verifies that the function raises a ValueError if the file is not marked as new
        and does not exist in the directory.
        """
        with self.assertRaises(ValueError):
            verified_file_name(self.dir, self.new_file_name)

    def test_verified_file_name_is_new_and_file_is_directory(self):
        """Test the `verified_file_name` function when the file is new but is actually a directory.
        Verifies that the function raises a ValueError if the file is marked as new
        but the provided name is an existing directory.
        """
        with self.assertRaises(ValueError):
            verified_file_name(self.dir, self.dir, is_new=True)

    def test_verified_file_name_is_not_new_and_file_is_directory(self):
        """Test the `verified_file_name` function when
        the file is not new and is actually a directory.
        Verifies that the function raises a ValueError if the file is not marked as new
        but the provided name is an existing directory.
        """
        with self.assertRaises(ValueError):
            verified_file_name(self.dir, self.dir)
