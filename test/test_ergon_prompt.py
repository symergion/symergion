import unittest
from ergon.prompt import Prompt

from utils.setup_test import get_test_config


class TestPrompt(unittest.TestCase):
    """A test case for the Prompt class.
    This class tests the following functionalities of the Prompt class:
        - initialization,
        - appending,
        - string representation,
        - template access,
        - parameter retrieval.
    """

    def setUp(self):
        """Set up the test environment before each test method is run.
        Initializes a template dictionary with:
            - regex patterns for source,
            - regex patterns for destination,
            - call to action,
            - code starter
        Creates an instance of the Prompt class using:
            - the template,
            - initital prefix value,
            - initial prompt value,
            - initial _for_entity value
        """
        _, self.template = get_test_config()
        self.prompt = Prompt(
            self.template,
            "source_code\n\n",
            "test prompt",
            " for the above code"
        )

    def test_init(self):
        """Test the initialization of the Prompt class.
        Verifies that prompt:
            - instance is of type Prompt,
            - length of is 1,
            - last element is the expected string
            - prefix, body, suffix _for_entry are set correctly,
        """
        self.assertIsInstance(self.prompt, Prompt)
        self.assertIn("source_code", self.prompt.prefix)
        self.assertEqual(len(self.prompt), 1)
        self.assertEqual(self.prompt[-1], "test prompt")
        self.assertEqual(self.prompt.prefix, "source_code\n\n")
        self.assertEqual(self.prompt.body, "")
        self.assertEqual(self.prompt.suffix, "import unittest\n")
        self.assertEqual(self.prompt._for_entity, " for the above code")

    def test_append(self):
        """Test the append method of the Prompt class.
        Appends a new prompt to the existing prompt.
        Checks if:
            - length of the prompt is incremented by 1,
            - last element of the prompt is the appended string.
        """
        new_prompt = "new_prompt"
        self.prompt.append(new_prompt)

        self.assertEqual(len(self.prompt), 2)
        self.assertEqual(self.prompt[-1], new_prompt)

    def test_str(self):
        """Test the string representation of the Prompt class.
        Checks if the string representation of the prompt matches the expected format.
        """
        prompt_source = "source_code\n"
        task_cta = "# Create unittest TestCase for the above code"
        user_cta = "# test prompt\n"
        code_starter = f"{self.prompt.template.get('code_starter')}"
        prompt_str = f"{prompt_source}\n{task_cta}\n{user_cta}\n\n{code_starter}"

        self.assertEqual(str(self.prompt), prompt_str)

    def test_template(self):
        """Test the template property of the Prompt class.
        Verifies that the template property returns the template used during initialization.
        """
        self.assertEqual(self.prompt.template, self.template)

    def test_destination_pattern(self):
        """Test the destination pattern retrieval from the Prompt class.
        Checks if the destination pattern in the parameters matches the expected regex pattern.
        """
        destination = self.template.get("params").get("destination")
        self.assertEqual(self.prompt.params.get("destination"), destination)

    def test_initial_prompt(self):
        """Test the initial_prompt property of the Prompt class.
        Checks if the initial_prompt is generated correctly.
        """
        expected_initial_prompt = [
            "Create unittest TestCase for the above code",
            "test prompt"
        ]
        self.assertEqual(self.prompt.initial_prompt, expected_initial_prompt)

    def test_body(self):
        """Test the body property of the Prompt class.
        Checks if the body is generated correctly.
        """
        self.prompt.append("new_prompt")
        expected_body = "# new_prompt"

        self.assertEqual(self.prompt.body, expected_body)

    def test_suffix(self):
        """Test the suffix property of the Prompt class.
        Checks if the suffix is generated correctly.
        """
        self.assertEqual(self.prompt.suffix, "import unittest\n")

    def test_comments(self):
        """Test the comments property of the Prompt class.
        Checks if the comments are generated correctly.
        """
        expected_comments = [
            "Create unittest TestCase for the above code\ntest prompt",
        ]
        self.assertEqual(self.prompt.comments, expected_comments)

    def test_format_reasoning(self):
        """Test the format_reasoning method of the Prompt class.
        Checks if the reasoning is formatted correctly.
        """
        reasoning = "Reasoning"
        expected_reasoning = "\nReasoning\nBeing laconic and return code only is at high importance"

        self.assertEqual(self.prompt.format_reasoning(reasoning), expected_reasoning)
