import time
import torch
import regex as re

from symerg.base import SymErg
from utils.cache import in_memory_cache


class SymErgReasoner(SymErg):
    """A class for generating reasonings based on a given prompt
    using a pre-trained language model.

    Attributes:
        ergons (list of Ergon): attached Ergons,
        model (transformers.AutoModelForCausalLM): loaded pre-trained model,
        tokenizer (transformers.AutoTokenizer): loaded pre-trained tokenizer.

    Readonly Attributes:
        name_or_path (str): name or path of the pre-trained model,
        trait (str): trait of the SymErg instance.
    """

    def __init__(self, checkpoint, **symerg_config):
        """Initialize the SymErg instance.

        Args:
            checkpoint (dict): a dictionary containing:
                                - the necessary configuration,
                                - weights for the model.
            symerg_config (dict): SymErg configuration parameters.

        Raises:
            ValueError:
                - if no reasoning start tokens are provided,
                - if no reasoning stop tokens are provided.
        """
        super().__init__(checkpoint, **symerg_config)

        self.reasoning_start_tokens = checkpoint.get("reasoning_start_tokens")
        self.reasoning_stop_tokens = checkpoint.get("reasoning_stop_tokens")

    @property
    def reasoning_start_tokens(self):
        """Get the reasoning section start tokens.

        Returns:
            list of int: sequence of tokens that marks the start of reasoning.
        """
        return self._reasoning_start_tokens

    @reasoning_start_tokens.setter
    def reasoning_start_tokens(self, start_tokens):
        """Set the reasoning section start tokens.

        Raises:
            ValueError: if no reasoning start tokens are provided,
        """
        if not start_tokens:
            raise ValueError(f"No reasoning_start_tokens are provided for {self.name_or_path}")
        self._reasoning_start_tokens = start_tokens

    @property
    def start_tokens_len(self):
        """Get the length of the reasoning start tokens.

        Returns:
            int: the number of tokens in the reasoning start sequence.
        """
        return len(self.reasoning_start_tokens)

    @property
    def reasoning_stop_tokens(self):
        """Get the reasoning section stop tokens.

        Returns:
            list of int: sequence of tokens that marks the stop of reasoning.
        """
        return self._reasoning_stop_tokens

    @reasoning_stop_tokens.setter
    def reasoning_stop_tokens(self, stop_tokens):
        """Set the reasoning section stop tokens.

        Raises:
            ValueError: if no reasoning stop tokens are provided,
        """
        if not stop_tokens:
            raise ValueError(f"No reasoning_stop_tokens are provided for {self.name_or_path}")
        self._reasoning_stop_tokens = stop_tokens

    @property
    def stop_tokens_len(self):
        """Get the length of the reasoning stop tokens.

        Returns:
            int: the number of tokens in the reasoning stop sequence.
        """
        return len(self.reasoning_stop_tokens)

    def update(self, message):
        """Update the reasoner with a new message.

        Args:
            message (dict): The message to be processed.

        Returns:
            None: this method is not implemented.
        """
        return NotImplemented

    def _notify(self, message):
        """Notify the reasoner listeners about a new message.

        Args:
            message (dict): The message to be processed.

        Returns:
            None: this method is not implemented.
        """
        return NotImplemented

    def stop_at_token(self, length, ids, _):
        """Determine whether to stop generation based on the last tokens generated.

        Args:
            length (int): the current length of the generated tokens.
            ids (torch.Tensor): The tensor containing the generated token IDs.
            _ (any): an additional argument that is not used.

        Returns:
            bool: True if the stop tokens are detected, False otherwise.
        """
        stop_tokens = ids[-1][-self.stop_tokens_len:] == torch.Tensor(self.reasoning_stop_tokens)
        return min(stop_tokens).item() and ids.shape[-1] > length + self.stop_tokens_len

    @in_memory_cache("_response_cache_size")
    def generate(self, prompt):
        """Generate a response based on the given prompt.

        Args:
            prompt (str): the input prompt for which the response is to be generated.

        Returns:
            str: The generated response after processing the prompt.
        """
        chat = [{"role": "user", "content": prompt}]
        encodings = self.tokenizer.apply_chat_template(
            chat, return_tensors="pt",
            thinking=True,
            return_dict=True,
            add_generation_prompt=True
        )
        encodings_len = encodings.get("input_ids").shape[-1]
        max_new_tokens, _ = self.get_max_new_tokens(encodings_len)

        if max_new_tokens <= 0:
            return ""

        eos_token_id = self.config.eos_token_id
        self.eval()

        start_time = time.time()
        with torch.no_grad():
            generated_ids = self.model.generate(
                **encodings,
                max_new_tokens=max_new_tokens,
                pad_token_id=eos_token_id,
                stopping_criteria=[lambda ids, _: self.stop_at_token(encodings_len, ids, _)]
            )
        end_time = time.time()
        delta = round(end_time - start_time, 1)
        print(f"{self.name_or_path} returned {generated_ids.shape[-1]} tokens")

        # remove start and stop reasoning sequences
        output_ids = generated_ids[0, encodings_len:]

        if torch.equal(output_ids[-self.stop_tokens_len:], torch.tensor(self.reasoning_stop_tokens)):
            output_ids = output_ids[:-self.stop_tokens_len]

        if torch.equal(output_ids[:self.start_tokens_len], torch.tensor(self.reasoning_start_tokens)):
            output_ids = output_ids[self.start_tokens_len:]

        print(f"It took {delta}s to generate {output_ids.shape[-1]} new tokens")
        output = self.tokenizer.decode(
            output_ids,
            skip_special_tokens=True
        )

        # remove blocks of code if any in the reasoning part
        output = re.sub(r'(?s)\s*```\p{L}+\n.*?```\n', '', output)
        return output
