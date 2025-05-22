import os.path
import regex as re

from utils import file_exists
from utils import verified_file_name
from utils import read_text_file
from utils.list import CustomList

from git.branches import Branches
from ergon.base import Ergon
from ergon.prompt import Prompt


class ErgonCode(Ergon):
    """ErgonCode class:
        - observe and complete action requests from SymErg

    Readonly Attributes:
        name (str): Ergon name, name of the feature branch.
    """
    patterns = {
        "class_name": r"(?:^|[\n]+)class\s+([\p{L}\p{N}]+)\(",
        "function_name": r"(?:^|[\n]+)def\s+([\p{L}\p{N}_]+)\("
    }

    def __init__(self, task_type, template, repo, feature_branch, reasoners=None):
        """Initialize the ErgonCode instance.

        Args:
            task_type (str): type of the task to be performed,
            template (dict): template configuration for the task,
            repo (Repo): repository object where the task will be performed,
            feature_branch (str): name of the feature branch,
            reasoners (list of SymErgReasoner, optional) reasoners to be used.
        """
        super().__init__(name=feature_branch)

        self._task_type = task_type
        self._template = template
        self._repo = repo
        self._branches = Branches(repo, feature_branch)
        self._reasoners = reasoners if reasoners else []

        self._notes = []
        self._destination_file = None
        self._source_file = None
        self._prompt = None

    @property
    def repo(self):
        """Get the repository object.

        Returns:
            Repo: repository object.
        """
        return self._repo

    @property
    def task_type(self):
        """Get the task type.

        Returns:
            str: task type.
        """
        return self._task_type

    @property
    def branches(self):
        """Get the branches object.

        Returns:
            Branches: branches.
        """
        return self._branches

    @property
    def reasoners(self):
        """Get the list of reasoners.

        Returns:
            list of SymErgReasoner: reasoners.
        """
        return self._reasoners

    @property
    def notes(self):
        """Get the list of notes.

        Returns:
            list of tuple[str, str]: notes.
        """
        return self._notes

    @property
    def source_file(self):
        """Get the source file path.

        Returns:
            str: Source file path.
        """
        return self._source_file

    @source_file.setter
    def source_file(self, source_file):
        """Set the source file path after verification.

        Args:
            source_file (str): path to the source file.
        """
        self._source_file = verified_file_name(self.repo.local, source_file)

    @property
    def destination_file(self):
        """Get the destination file path.

        Returns:
            str: destination file path.
        """
        return self._destination_file

    @destination_file.setter
    def destination_file(self, destination_file):
        """Set the destination file path after verification.

        Args:
            destination_file (str): path to the destination file.
        """
        self._destination_file = verified_file_name(self.repo.local, destination_file, is_new=True)

    @property
    def template(self):
        """Get the template configuration.

        Args:
            dict: template configuration.
        """
        return self._template

    @property
    def params(self):
        """Get the parameters from the template.

        Returns:
            dict: parameters from the template.
        """
        return self.template.get("params")

    @property
    def prompt(self):
        """Get the prompt object.

        Returns:
            Prompt: prompt.
        """
        return self._prompt

    @prompt.setter
    def prompt(self, prompt):
        """Set the prompt object and generate reasoning based on it.

        Args:
            prompt (str): the prompt string.

        Raises:
            ValueError:
                - if no destination is specified in note,
                - if no source is specified in note.
        """
        if not re.search(self.params.get("destination"), prompt):
            raise ValueError("No destination, use `destination: destination/file/name`")

        kwargs = {
            "template": self.template,
            "prefix": "",
            "prompt": prompt
        }
        [self.destination_file] = re.findall(self.params.get("destination"), prompt)
        if file_exists(os.path.join(self.repo.local, self.destination_file)):
            destination_code = read_text_file(os.path.join(self.repo.local, self.destination_file))
            kwargs.update({"prefix": f"{kwargs.get('prefix')}{destination_code}\n\n"})

        if self.params.get("source") and not re.search(self.params.get("source"), prompt):
            raise ValueError(f"Specify `source: source/file/name` for {self.task_type} task.")

        if self.params.get("source"):
            [self.source_file] = re.findall(self.params.get("source"), prompt)
            source_code = read_text_file(os.path.join(self.repo.local, self.source_file))
            kwargs.update({"prefix": f"{kwargs.get('prefix')}{source_code}\n\n"})

            entity = ""
            class_names = re.findall(self.patterns.get("class_name"), source_code)
            entity += ", ".join([f" for the class {c_name}" for c_name in class_names])

            function_names = re.findall(self.patterns.get("function_name"), source_code)
            entity += ", ".join([f" for the function {f_name}" for f_name in function_names])

            kwargs.update({"for_entity": entity if len(entity) > 0 else " for the above code"})

        self._prompt = Prompt(**kwargs)

    @prompt.deleter
    def prompt(self):
        """Delete the prompt object and reset related properties.
        """
        self.destination_file = None
        self.source_file = None
        del self._prompt

    @property
    def initial_message(self):
        """Get Ergon related SymErg branches init prompt message.

        Returns:
            str: Ergon init prompt message.

        Raises:
            ValueError: if initial prompt commit messages are
                        vary across Ergon related SymErg branches.
        """
        messages = [self.get_symerg_messages(branch) for branch in self.branches]
        unique_init_messages = set((message[0] for message in messages if len(message) > 0))

        if len(unique_init_messages) > 1:
            raise ValueError(f"Commit messages mismatch for {self.name} task related branches.")

        return unique_init_messages.pop() if len(unique_init_messages) == 1 else None

    def get_symerg_messages(self, branch):
        """Get symerg meaningful commmit messages from SymErg branch

        Args:
            symerg_branch (str): name of the SymErg or Ergon branch.

        Returns:
            CustomList: commit messages.
        """
        messages = []

        if branch.endswith(self.name) and not self.name == branch:
            messages = self.repo.get_objects_messages(f"{self.name}..{branch}")

        elif self.name == branch:
            messages = self.repo.get_ergon_branch_messages(branch)

        reverting_messages = [m for m in messages if re.search("^Revert: ", m)]

        for reverting_message in reverting_messages:
            messages.remove(reverting_message)
            [message] = re.findall("^Revert: ((?s).+)", reverting_message)

            if messages.count(message) > 0:
                messages.remove(message)

        messages.reverse()
        return CustomList(messages)

    def update(self, message):
        """Update the ErgonCode instance based on the received message.

        Args:
            message (dict): message containing update details.
        """
        topic_branch = message.get("topic")
        if self.name not in topic_branch:
            return

        payload = message.get("payload")

        if isinstance(payload, str):
            self.checkout(topic_branch)
            comment = message.get("comment")
            self.respond(topic_branch, payload, comment)

        elif isinstance(payload, Ergon):
            if topic_branch in self.branches:
                self.branches.remove(topic_branch)

            else:
                self.branches.append(topic_branch)

    def checkout(self, branch):
        """Checkout the specified branch.

        Args:
            branch (str): name of the branch to checkout.
        """
        if branch in self.branches:
            self.repo.checkout(branch)

        elif branch in self.branches.remotes:
            self.branches.append(branch)

        else:
            self.branches.append(branch, is_new=True)

    def respond(self, branch, payload, comment):
        """Respond to the given branch
        with the provided response and commit message.

        Args:
            branch (str): name of the branch,
            payload (str): response content to write to the destination file,
            comment (str): commit message for the change.
        """
        destination_path = os.path.join(self.repo.local, self._destination_file)
        with open(destination_path, "w", encoding="utf-8") as f:
            f.write(payload)

        model = branch.removesuffix(f"_{self.name}")
        self.repo.set_user(model)
        self.repo.add(self.destination_file)
        self.repo.commit(comment)
