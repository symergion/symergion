import unittest
import json
import os

from symergion.config import Config


class TestConfig(unittest.TestCase):
    """A test case for the Config class in the symergion.config module.
    """
    def setUp(self):
        """Set up the test environment by creating a temporary JSON file.
        """
        self.json_data = {
            "name": "Name"
        }
        with open("test.json", "w", encoding="utf-8") as f:
            json.dump(self.json_data, f)

    def tearDown(self):
        """Clean up the test environment by removing the temporary JSON file.
        """
        os.remove("test.json")

    def test_init(self):
        """Test the initialization of the Config class with a dictionary.
        This test checks that the Config object is created successfully and
        that its attributes match those provided in the input dictionary.
        """
        config = Config(self.json_data)

        self.assertIsInstance(config, Config)
        self.assertEqual(config.name, self.json_data.get("name"))

    def test_config_loaded_from_json_file(self):
        """Test the loading of a Config object from a JSON file.
        This test checks that the Config object is created successfully from a
        JSON file and that its attributes match those in the file.
        """
        config = Config.from_json("test.json")

        self.assertIsInstance(config, Config)
        self.assertEqual(config.name, self.json_data.get("name"))

    def test_getattr_nonexistent(self):
        """Test the behavior of the Config class when accessing a non-existent attribute.
        This test checks that accessing a non-existent attribute returns an empty dictionary.
        """
        config = Config.from_json("test.json")

        self.assertIsNone(config.wrong_attribute)
