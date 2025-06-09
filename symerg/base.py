import math
from abc import abstractmethod
from transformers import AutoModelForCausalLM, AutoTokenizer

from observer import Observer
from utils import in_memory_cache


class SymErg(Observer):
    """Base SymErg abstract class.
    Any symerg implementation should derive from this class and
    provide implementations for the abstract methods `update` and `notify`.

    Responsibilities of a SymErg instance include:
        - observe and complete action requests from SymErgion
        - load tokenizer and model from pretrained
        - move itself to specified device
        - attach, detach Ergons
        - request Ergons to complete actions
    """

    def __init__(self, checkpoint, model_cache_size, response_cache_size, ntokens):
        """Initialize the SymErg instance.

        Args:
            checkpoint (dict): the checkpoint specification.
            model_cache_size (int): the size of the loaded models cache.
            response_cache_size (int): the size of the response cache.
            ntokens (int): the number of tokens.
        """
        self._checkpoint = checkpoint
        self._model_cache_size = model_cache_size
        self._response_cache_size = response_cache_size
        self._ntokens = ntokens

        self._ergons = []
        self._model = None
        self._tokenizer = None

    @property
    def name_or_path(self):
        """Get the name or path of the pre-trained model.

        Returns:
            str: the name or path of the model.
        """
        return self._checkpoint.get("name_or_path")

    @property
    def ergons(self):
        """Get the attached Ergons.

        Returns:
            list of Ergon: attached Ergons.
        """
        return self._ergons

    @property
    def model(self):
        """Get the pre-trained model.
        If the model is not already loaded, it will be loaded from the pre-trained checkpoint.

        Returns:
            transformers.AutoModelForCausalLM: model.
        """
        if self._model:
            return self._model
        return self.get_model(self.name_or_path)

    @model.setter
    def model(self, model):
        """Set the pre-trained model.

        Args:
            model (transformers.AutoModelForCausalLM): the pre-trained model to set.
        """
        self._model = model

    @property
    def tokenizer(self):
        """Get the pre-trained tokenizer.
        If the tokenizer is not already loaded, it will be loaded from the pre-trained checkpoint.

        Returns:
            transformers.AutoTokenizer: the pre-trained tokenizer.
        """
        if self._tokenizer:
            return self._tokenizer
        return self.get_tokenizer(self.name_or_path)

    @tokenizer.setter
    def tokenizer(self, tokenizer):
        """Set the pre-trained tokenizer.

        Args:
            tokenizer (transformers.AutoTokenizer): the pre-trained tokenizer to set.
        """
        self._tokenizer = tokenizer

    @property
    def trait(self):
        """Get the trait of the SymErg instance.

        Returns:
            str: the trait of the SymErg instance.
        """
        return self._checkpoint.get("trait")

    def get_max_new_tokens(self, encodings_len):
        """Calculate the maximum number of new tokens that can be generated.

        Args:
            encodings_len (int): The length of the encoded input.
        Returns:
            tuple[int, int]: a tuple containing:
                            - the estimated maximum number of new tokens,
                            - the capacity.
        """
        capacity = self.config.max_position_embeddings - encodings_len
        capacity_diff = capacity - self._ntokens
        estimate = capacity - capacity_diff * math.exp(-encodings_len / capacity_diff)
        return round(estimate), capacity

    @in_memory_cache("_model_cache_size")
    def get_model(self, name_or_path):
        """Load the pre-trained model from the specified checkpoint.

        Args:
            name_or_path (str): the name or path of the checkpoint.

        Returns:
            transformers.AutoModelForCausalLM: the pre-trained model.
        """
        print(f"Model to be loaded: {name_or_path}")
        return AutoModelForCausalLM.from_pretrained(name_or_path)

    @in_memory_cache("_model_cache_size")
    def get_tokenizer(self, name_or_path):
        """Load the pre-trained tokenizer from the specified checkpoint.

        Args:
            name_or_path (str): The name or path of the checkpoint.

        Returns:
            transformers.AutoTokenizer: the pre-trained tokenizer.
        """
        return AutoTokenizer.from_pretrained(name_or_path)

    def attach_ergon(self, ergon):
        """Attach an Ergon to the SymErg instance.

        Args:
            ergon (Ergon): the Ergon to attach.
        """
        if ergon not in self.ergons:
            self._ergons.append(ergon)

    def detach_ergon(self, ergon):
        """Detach an Ergon from the SymErg instance.

        Args:
            ergon (Ergon): the Ergon to detach.
        """
        if ergon in self.ergons:
            self._ergons.pop(self.ergons.index(ergon))

    def __getattr__(self, attr):
        """Delegate attribute access to the underlying model.

        Args:
            attr (str): the attribute name.

        Returns:
            Any: the value of the attribute.
        """
        return getattr(self.model, attr)

    @abstractmethod
    def update(self, message):
        """Update the SymErg instance with a new message.

        Args:
            message (dict): the message to update with.

        Raises:
            NotImplementedError: this method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def _notify(self, message):
        """Notify the SymErg instance listeners about a new message.

        Args:
            message (dict): the message to notify about.

        Raises:
            NotImplementedError: this method must be implemented by subclasses.
        """
        raise NotImplementedError
