import unittest
from unittest.mock import Mock, patch

from transformers import AutoModelForCausalLM, AutoTokenizer

from symerg.base import SymErg


class TestSymErg(unittest.TestCase):
    """This class contains test methods to ensure that
    the SymErg class behaves as expected, including:
        - initialization,
        - model and tokenizer handling,
        - ergon attachment and detachment,
        - attribute access.
    """
    def setUp(self):
        """Set up the test environment.
        - creates subclasses of SymErg and Ergon for testing purposes
        and initializes instances of these classes with predefined values,
        - creates mock model and tokenizer.
        """
        class SymErgSub(SymErg):
            """Implements symerg deriving from SymErg abstract class.
            """
            def update(self, message):
                """Stub implementation"""
            def _notify(self, message):
                """Stub implementation"""
        self.checkpoint = {
            "name_or_path": "/test/model",
            "trait": "coding"
        }
        self.symerg = SymErgSub(self.checkpoint, 1, 10, 64)
        self.symerg.attach_ergon("efgh")
        self.model = Mock(spec=["existing_attribute"])
        self.tokenizer = Mock()

    def test_init(self):
        """Test the initialization of the SymErg instance.
        Ensures that the SymErg instance:
            - is correctly initialized,
            - its attributes are set as expected.
        """
        self.assertIsInstance(self.symerg, SymErg)
        self.assertEqual(self.symerg.name_or_path, self.checkpoint.get("name_or_path"))
        self.assertEqual(self.symerg.trait, self.checkpoint.get("trait"))
        self.assertIsInstance(self.symerg.ergons, list)
        self.assertEqual(len(self.symerg.ergons), 1)

    def test_model(self):
        """Test the retrieval of the SymErg model attribute.
        Ensures that:
            - AutoModelForCausalLM from_pretrained method is called to load model,
            - its called with SymErg name_or_path attribute provided as parameter.
        """
        with patch.object(AutoModelForCausalLM, "from_pretrained") as from_pretrained:
            self.symerg.model()
            from_pretrained.assert_called_once()
            from_pretrained.assert_called_with(self.symerg.name_or_path)

    def test_get_model(self):
        """Test the get_model method of the SymErg instance.
        Ensures that:
            - AutoModelForCausalLM from_pretrained method is called to load model,
            - its called with SymErg name_or_path attribute provided as parameter.
        """
        with patch.object(AutoModelForCausalLM, "from_pretrained") as from_pretrained:
            self.symerg.get_model(self.checkpoint.get("name_or_path"))
            from_pretrained.assert_called_once()
            from_pretrained.assert_called_with(self.checkpoint.get("name_or_path"))

    def test_set_model(self):
        """Test the set_model method of the SymErg instance.
        Ensures that the model is being successfuly assigned
        """
        self.assertIsNone(self.symerg._model)
        self.symerg.model = self.model
        self.assertEqual(self.symerg._model, self.model)

    def test_tokenizer(self):
        """Test the retrieval of the SymErg tokenizer attribute.
        Ensures that:
            - AutoTokenizer from_pretrained method is called to load tokenizer,
            - its called with SymErg name_or_path attribute provided as parameter.
        """
        with patch.object(AutoTokenizer, "from_pretrained") as from_pretrained:
            self.symerg.tokenizer()
            from_pretrained.assert_called_once()
            from_pretrained.assert_called_with(self.symerg.name_or_path)

    def test_get_tokenizer(self):
        """Test the get_tokenizer method of the SymErg instance.
        Ensures that:
            - AutoTokenizer from_pretrained method is called to load tokenizer,
            - its called with SymErg name_or_path attribute provided as parameter.
        """
        with patch.object(AutoTokenizer, "from_pretrained") as from_pretrained:
            self.symerg.get_tokenizer(self.checkpoint.get("name_or_path"))
            from_pretrained.assert_called_once()
            from_pretrained.assert_called_with(self.checkpoint.get("name_or_path"))

    def test_set_tokenizer(self):
        """Test the set_tokenizer method of the SymErg instance.
        Ensures that the tokenizer is being successfuly assigned
        """
        self.assertIsNone(self.symerg._tokenizer)
        self.symerg.tokenizer = self.tokenizer
        self.assertEqual(self.symerg._tokenizer, self.tokenizer)

    def test_attach_ergon(self):
        """Test the attachment of an Ergon instance to the SymErg instance.
        Ensures that the Ergon instance:
            - is correctly attached,
            - its attributes are set as expected.
        """
        self.symerg.attach_ergon("abcd")
        self.assertEqual(self.symerg.ergons[-1], "abcd")

    def test_detach_ergon(self):
        """Test the detachment of an Ergon instance from the SymErg instance.
        Ensures that the Ergon instance is correctly detached.
        """
        self.symerg.detach_ergon("efgh")
        self.assertEqual(len(self.symerg.ergons), 0)

    def test_ergons(self):
        """Test the retrieval of the list of attached Ergons.
        Ensures that the list of attached Ergons matches the internal list.
        """
        self.assertListEqual(self.symerg.ergons, ["efgh"])

    def test_getattr_non_existing(self):
        """Test the behavior of accessing a non-existing attribute.
        Ensures that accessing a non-existing attribute raises an AttributeError.
        """
        self.symerg._model = self.model
        with self.assertRaises(AttributeError):
            self.symerg.not_existing_method()

    def test_getattr_existing(self):
        """Test the behavior of accessing an existing SymErg and model attributes.
        Ensures that accessing an existing attribute returns the correct value.
        """
        self.symerg._model = self.model
        self.assertEqual(self.symerg.name_or_path, self.checkpoint.get("name_or_path"))
        self.assertEqual(self.symerg.existing_attribute, self.model.existing_attribute)
