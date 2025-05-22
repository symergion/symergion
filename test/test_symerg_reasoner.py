import unittest
from unittest.mock import Mock

import torch

from symergion.config import Config
from symerg.reasoner import SymErgReasoner


class TestSymErgReasoner(unittest.TestCase):
    """This class tests various functionalities of the SymErgReasoner class, including:
        - initialization,
        - update,
        - notify,
        - stop_at_token,
        - generate.
    """

    def setUp(self):
        """Set up the test environment before each test method is run.
        Instantiates the SymErgReasoner with a mock tokenizer and predefined configurations.
        Creates mock model.
        """
        self.checkpoint = {
            "name_or_path": "/test/model",
            "trait": "coding",
            "reasoning_start_tokens": [1, 2, 3],
            "reasoning_stop_tokens": [4, 5, 6]
        }
        self.cache_size = 1
        self.response_cache_size = 10
        self.ntokens = 100
        self.symerg_reasoner = SymErgReasoner(
            self.checkpoint,
            **{
                "cache_size": self.cache_size,
                "response_cache_size": self.response_cache_size,
                "ntokens": self.ntokens
            }
        )

        self.model = Mock("config")
        self.model.config = Config.from_json(f"{self.symerg_reasoner.name_or_path}/config.json")
        self.model.attach_mock(lambda *args, **kwargs: None, "eval")
        self.model.attach_mock(lambda *args, **kwargs: torch.tensor([[1, 2, 3, 0, 0, 0, 4, 5, 6]]), "generate")

        self.symerg_reasoner.tokenizer = Mock()
        test_ids = torch.tensor([[1, 1, 1]], dtype=torch.int32)
        test_mask = torch.tensor([[1, 1, 1]], dtype=torch.int32)
        test_encodings = {'input_ids': test_ids, 'attention_mask': test_mask}
        self.symerg_reasoner.tokenizer.apply_chat_template = lambda *args, **kwargs: test_encodings
        self.symerg_reasoner.tokenizer.decode = lambda *args, **kwargs: str(args[0].shape.numel())

    def test_init(self):
        """Test the initialization of the SymErgReasoner.
        """
        self.assertEqual(self.symerg_reasoner.reasoning_start_tokens, [1, 2, 3])
        self.assertEqual(self.symerg_reasoner.reasoning_stop_tokens, [4, 5, 6])
        self.assertEqual(self.symerg_reasoner.start_tokens_len, 3)
        self.assertEqual(self.symerg_reasoner.stop_tokens_len, 3)

    def test_update(self):
        """Test the update method of the SymErgReasoner.
        Checks if the update method returns NotImplemented.
        """
        message = "test message"
        self.assertEqual(self.symerg_reasoner.update(message), NotImplemented)

    def test_notify(self):
        """Test the notify method of the SymErgReasoner.
        Checks if the notify method returns NotImplemented
        """
        message = "test message"
        self.assertEqual(self.symerg_reasoner._notify(message), NotImplemented)

    def test_stop_at_token(self):
        """Test the stop_at_token method of the SymErgReasoner.
        Verifies that the method correctly
        identifies when to stop based on the presence of stop tokens.
        """
        length = 6
        ids = torch.Tensor([[1, 2, 3, 4, 5, 6, 7, 4, 5, 6]])
        self.assertTrue(self.symerg_reasoner.stop_at_token(length, ids, None))

    def test_generate(self):
        """Test the generate method of the SymErgReasoner.
        Ensures that the generate method returns expected response.
        """
        self.symerg_reasoner.model = self.model
        prompt = "test prompt"
        response = self.symerg_reasoner.generate(prompt=prompt)
        self.assertEqual(response, '3')
