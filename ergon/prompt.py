import regex as re


class Prompt(list):
    """A class representing a prompt, which is
    a list of strings with additional properties.
    """

    def __init__(self, template, prefix, prompt, for_entity=None):
        """Initializes a new instance of the Prompt class.

        Args:
            template (dict): a dictionary containing template information,
            prefix (str): a string representing the prefix of the prompt,
            prompt (str): the initial prompt string,
            for_entity (str, optional): a string representing the entity
            for which the prompt call to action is intended.
        """
        super().__init__([])
        self._template = template
        self._prefix = prefix
        self._for_entity = for_entity
        super().append(prompt)

    @property
    def template(self):
        """Gets the template associated with the prompt.

        Returns:
            dict: the template dictionary.
        """
        return self._template

    @property
    def params(self):
        """Gets the parameters from the template.

        Returns:
            dict: the parameters dictionary.
        """
        return self.template.get("params")

    @property
    def prefix(self):
        """Gets the prefix of the prompt.

        Returns:
            str: the prefix string.
        """
        return self._prefix

    @property
    def initial_prompt(self):
        """Generates the initial prompt based on the template and entity.

        Returns:
            list: the initial prompt.

        Raises:
            ValueError: if no call_to_action is provided in the template.
        """
        if not self.template.get("call_to_action"):
            raise ValueError("No call_to_action is provided in config.")

        if len(self) == 0:
            return ""

        note = self[0]

        for param in self.params.values():
            note = " ".join({g for g in re.split(param, note) if g} - set(re.findall(param, note)))

        call_to_action = f"{self.template.get('call_to_action')}"

        if self.params.get("source") and self._for_entity:
            call_to_action = f"{call_to_action}{self._for_entity}"

        prompt_rows = [row for row in note.split("\n") if row]
        prompt_rows.insert(0, call_to_action)
        return prompt_rows

    @property
    def body(self):
        """Gets the body of the prompt.

        Returns:
            str: the body of the prompt.
        """
        return "\n".join([f"# {row}" for row in self[1:]])

    @property
    def suffix(self):
        """Gets the suffix of the prompt.

        Returns:
            str: the suffix of the prompt.
        """
        return self.template.get("code_starter", "")

    @property
    def comments(self):
        """Generates the comments for the prompt.

        Returns:
            list: the comments.
        """
        prompt_comments = ["\n".join(self.initial_prompt)]
        prompt_comments.extend(self[1:])
        return prompt_comments

    def format_reasoning(self, reasoning):
        """Formats reasoning to be added to initial prompt.

        Args:
            reasoning (str): reasoning to be formatted.

        Returns:
            str: formatted reasoning.
        """
        if reasoning[0] != "\n":
            reasoning = f"\n{reasoning}"

        if not reasoning.endswith("\nBeing laconic and return code only is at high importance"):
            reasoning = f"{reasoning}\nBeing laconic and return code only is at high importance"

        return reasoning

    def __str__(self):
        """Returns a string representation of the prompt.

        Returns:
            str: the prompt.
        """
        prefix = self.prefix
        initial_prompt = "\n".join([f"# {row}" for row in self.initial_prompt if row])
        return f"{prefix}{initial_prompt}\n\n{self.body}\n{self.suffix}"
