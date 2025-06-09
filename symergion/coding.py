import os.path
import regex as re

from git.branches import Branches
from symergion.base import SymErgion
from symerg.coder import SymErgCoder
from symerg.reasoner import SymErgReasoner
from ergon.code import ErgonCode

from utils.flatten import flatten
from utils.list import CustomList


class SymErgionCoding(SymErgion):
    """SymErgioniCoding class:
        - complete actions based on updates
        - attach, detach SymErgs
        - attach, detach Ergons
        - request Ergons to complete actions

    Attributes:
        symergs (list of SymErg): attached SymErgs,
        ergons (list of Ergon): attached Ergons.
    """

    def __init__(self, repo, config):
        """Initializes the SymErgionCoding instance.

        Args:
            repo (Repository): the repository object.
            config (Config): configuration object containing necessary settings.

        Raises:
            ValueError:
                - if no model_cache_size is provided,
                - if no response_cache_size is provided,
                - if no ntokens is provided,
                - if no task_branch_spec is provided,
                - if no templates are provided,
                - if no checkpoints are provided,
        """
        super().__init__()

        self._repo = repo

        if not config.model_cache_size:
            raise ValueError("No model_cache_size is provided in config.")
        if not config.response_cache_size:
            raise ValueError("No response_cache_size is provided in config.")
        if not config.ntokens:
            raise ValueError("No ntokens is provided in config.")
        self._config = config

        if not config.task_branch_spec:
            raise ValueError("No task_branch_spec is provided in config.")
        self._task_branch_spec = config.task_branch_spec

        if not config.templates:
            raise ValueError("No templates are provided in config.")
        self._templates = config.templates

        if not config.checkpoints:
            raise ValueError("No checkpoints are provided in config.")
        self._checkpoints = config.checkpoints

        self._branches = Branches(self.repo)
        self._notes = []

    @property
    def task_branch_spec(self):
        """Get the task branch specification.

        Returns:
            str: a task branch specification.
        """
        return self._task_branch_spec

    @property
    def checkpoints(self):
        """Get the checkpoints configuration.

        Returns:
            list: the checkpoints.
        """
        return self._checkpoints

    @property
    def feature_names_pattern(self):
        """Get regex pattern for matching feature names.

        Returns:
            str: a regex pattern for matching feature names.
        """
        return fr"({'|'.join(self.feature_names)})"

    @property
    def supported_coders(self):
        """Get regex pattern for matching supported coders.

        Returns:
            str: a regex pattern for matching supported coders.
        """
        if len(self.coders) > 0:
            coders_paths = [os.path.basename(coder.name_or_path) for coder in self.coders]
            return fr"^({'|'.join(coders_paths)})"
        return None

    @property
    def supported_tasks(self):
        """Get regex pattern for matching supported tasks.

        Returns:
            str: a regex pattern for matching supported tasks.
        """
        return fr"({'|'.join(self._templates.keys())})"

    @property
    def repo(self):
        """Get the repository object.

        Returns:
            Repo: a repository.
        """
        return self._repo

    @property
    def branches(self):
        """Get branches object.

        Returns:
            Branches: the branches object.
        """
        return self._branches

    @property
    def ergon_branches(self):
        """Get all ergons branches.

        Returns:
            CustomList of Branches: the ergons branches.
        """
        return CustomList(flatten([ergon.branches for ergon in self.ergons]))

    @property
    def feature_names(self):
        """Get feature names.

        Returns:
            list of str: feature names.
        """
        return [ergon.name for ergon in self.ergons]

    @property
    def notes(self):
        """Get notes.

        Returns:
            list of tuple: notes
        """
        return self._notes

    @property
    def ergon_notes(self):
        """Get all ergons notes.

        Returns:
            list of tuple: notes.
        """
        return flatten([ergon.notes for ergon in self.ergons])

    @property
    def coders(self):
        """Get SymErgion coders.

        Returns:
            list of SymErg: SymErgs with the trait 'coding'.
        """
        return [symerg for symerg in self.symergs if symerg.trait == "coding"]

    @property
    def reasoners(self):
        """Get SymErgion reasoners.

        Returns:
            list of SymErg: SymErgs with the trait 'reasoning'.
        """
        return [symerg for symerg in self.symergs if symerg.trait == "reasoning"]

    def sync_with_commits(self, ergon):
        """Synchronizes Ergon with commits by identifying removed notes and notifying accordingly.

        Args:
            ergon (Ergon): the Ergon object to synchronize.
        """
        removed_notes_messages = set()

        for branch in ergon.branches:
            if branch != ergon.name:
                meaning_messages = ergon.get_symerg_messages(branch)
                removed_notes_messages |= set(meaning_messages) - set(ergon.prompt.comments)

        if len(removed_notes_messages) > 0:
            comment = "\n".join([f"Revert: {rnm}" for rnm in removed_notes_messages])
            message = {
                "topic": ergon.name,
                "payload": ergon.prompt,
                "comment": comment
            }
            self._notify(message)

    def instantiate_symerg(self, checkpoint):
        """Instantiates a SymErg based on the provided checkpoint.

        Args:
            checkpoint (dict): The checkpoint configuration.

        Returns:
            SymErg: An instantiated SymErg object.

        Raises:
            ValueError: if specified checkpoint trait is not supported.
        """
        symerg_names = [symerg.name_or_path for symerg in self.symergs]

        if checkpoint.get("name_or_path") in symerg_names:
            return self.symergs[symerg_names.index(checkpoint.get("name_or_path"))]

        symerg_config = {
            "model_cache_size": self._config.model_cache_size,
            "response_cache_size": self._config.response_cache_size,
            "ntokens": self._config.ntokens
        }
        trait = checkpoint.get("trait")

        if trait == "coding":
            return SymErgCoder(checkpoint, **symerg_config)

        if trait == "reasoning":
            return SymErgReasoner(checkpoint, **symerg_config)

        raise ValueError(f"Trait {trait} is not supported")

    def instantiate_ergon(self, name):
        """Instantiates an Ergon based on the provided name.

        Args:
            name (str): the name of the Ergon.

        Returns:
            Ergon: an instantiated Ergon object.

        Raises:
            ValueError: if no supported type task is specified in note.
        """
        if not re.search(self.supported_tasks, name):
            raise ValueError(f"No supported type ({self.supported_tasks}) for `{name}`")
        [task_type] = re.findall(self.supported_tasks, name)

        ergon = ErgonCode(
            task_type=task_type,
            template=self._templates.get(task_type),
            repo=self.repo,
            feature_branch=name,
            reasoners=self.reasoners
        )
        return ergon

    def decomission_ergon(self, ergon):
        """Decommissions the given Ergon by notifying relevant SymErgs and clearing branches.

        Args:
            ergon (Ergon): the Ergon object to decommission.
        """
        message = {
            "topic": ergon.name,
            "payload": ergon
        }
        coders = [coder for coder in self.coders if ergon in coder.ergons]
        self._notify(message, coders)
        ergon.branches.clear()

    def _extract_feature_name(self, topic_branch):
        """Extracts the feature name from the topic branch using a regex pattern.

        Args:
            topic_branch: the topic branch name.

        Returns:
            str: the extracted feature name.
        """
        feature_name = re.findall(self.feature_names_pattern, topic_branch).pop()
        return feature_name

    def _get_not_handled_coders(self, ergon):
        """Retrieves a list of coders that have not handled the given Ergon.

        Args:
            ergon (Ergon): the Ergon object.

        Returns:
            list of Ergon: unhandled coders.
        """
        coders = []

        for coder in self.coders:
            coder_branch = f"{os.path.basename(coder.name_or_path)}_{ergon.name}"

            if coder_branch not in ergon.branches.remotes:
                coders.append(coder)
            elif ergon.prompt.comments not in ergon.get_symerg_messages(coder_branch):
                coders.append(coder)

        return coders

    def _notify(self, message, symergs=None):
        """Notifies the specified SymErgs with the given message.
        If no SymErgs specified, notifies all coders.

        Args:
            message (dict): the message to notify.
            symergs (list of SymErgs): SymErgs to notify.
        """
        coders = symergs if isinstance(symergs, list) else self.coders
        coders_names = [c.name_or_path for c in coders]
        print(f"{coders_names} coders will be updated with the following message:\n{message}")

        for coder in coders:
            coder.update(message)

    def _new_feature_branch(self, topic_branch):
        """Handles the creation of a new feature branch.

        Args:
            topic_branch (str): the feature branch name.
        """
        ergon = self.instantiate_ergon(topic_branch)
        new_topic = {
            "topic": topic_branch,
            "payload": ergon
        }
        self._notify(new_topic)

    def _delete_feature_branch(self, topic_branch):
        """Handles the deletion of a feature branch.

        Args:
            topic_branch (str): the feature branch name.
        """
        [ergon] = [ergon for ergon in self.ergons if ergon.name == topic_branch]
        self.decomission_ergon(ergon)

    def _new_model_branch(self, topic_branch):
        """Handles the creation of a new model branch.

        Args:
            topic_branch (str): the model branch name.
        """
        feature_name = self._extract_feature_name(topic_branch)
        [ergon] = [ergon for ergon in self.ergons if ergon.name == feature_name]
        message = {
            "topic": topic_branch,
            "payload": ergon
        }
        coder_name = topic_branch.removesuffix(f"_{feature_name}")
        coder = [s for s in self.coders if coder_name == os.path.basename(s.name_or_path)]
        self._notify(message, coder)

    def _delete_model_branch(self, topic_branch):
        """Handles the deletion of a model branch.

        Args:
            topic_branch (str): the model branch name.
        """
        feature_name = self._extract_feature_name(topic_branch)
        [ergon] = [ergon for ergon in self.ergons if ergon.name == feature_name]
        message = {
            "topic": topic_branch,
            "payload": ergon
        }
        coder_name = topic_branch.removesuffix(f"_{feature_name}")
        coder = [s for s in self.coders if coder_name == os.path.basename(s.name_or_path)]
        self._notify(message, coder)

    def _update_with_payload(self, payload, ergon):
        """Updates the SymErgion with the given payload.

        Args:
            payload (dict): the payload data.
            ergon (Ergon): affiliated Ergon.

        Raises:
            ValueError: if action to be done is unclear
        """
        message = {
            "topic": ergon.name
        }
        coders = None

        # new message is added to prompt
        if ergon.prompt and payload.get("note_message") not in ergon.prompt:
            note_message = payload.get("note_message")
            ergon.prompt.append(note_message)
            message.update({"comment": note_message})
            coders = self._get_not_handled_coders(ergon)
            print(f"Note '{note_message}' will be processed.")

        # initial message is added
        elif not ergon.prompt:
            ergon.prompt = payload.get("note_message")
            comment = ergon.prompt.comments[-1]
            reasoning = ""

            if ergon.initial_message and ergon.initial_message.startswith(comment):
                print(f"{ergon.name} initial message reasoning to be loaded from commit message")
                reasoning += ergon.initial_message.replace(comment, "")

            else:
                reasoners = ", ".join((rsn.name_or_path for rsn in ergon.reasoners))
                print(f"{ergon.name} initial message reasoning to be generated by {reasoners}")
                reasoning += "\n".join((rsn.generate(str(ergon.prompt)) for rsn in ergon.reasoners))

            if len(reasoning) > 0:
                ergon.prompt[0] += ergon.prompt.format_reasoning(reasoning)
                print(f"{ergon.name} initial message is enriched with formatted reasoning")

            message.update({"comment": ergon.prompt.comments[-1]})
            coders = self._get_not_handled_coders(ergon)

        # existing message is removed from prompt
        elif ergon.prompt and payload.get("note_message") in ergon.prompt[1:]:
            note_message = payload.get("note_message")
            ergon.prompt.remove(note_message)
            print(f"'{note_message}' is removed from {ergon.name} prompt")
            message.update({"comment": f"Revert: {note_message}"})

        # initial message is removed
        elif ergon.prompt and payload.get("note_message") == ergon.prompt[0]:
            note_message = payload.get("note_message")
            ergon.prompt.remove(note_message)
            print(f"Initial message '{note_message}' is removed from {ergon.name} prompt")

            for coder_branch in ergon.branches.coders:
                self._delete_model_branch(coder_branch)

        else:
            raise ValueError

        message.update({"payload": ergon.prompt})
        self._notify(message, coders)

        if payload.get("note") not in ergon.notes:
            ergon.notes.append(payload.get("note"))
        else:
            ergon.notes.remove(payload.get("note"))

    def _add_note(self, payload):
        """Adds a note to the list of non-feature notes.

        Args:
            payload (tuple): note.
        """
        if payload not in self.notes:
            self.notes.append(payload)

    def _remove_note(self, payload):
        """Removes a note to the list of non-feature notes.

        Args:
            payload (tuple): note.
        """
        if payload in self.notes:
            self.notes.remove(payload)

    def _update_with_no_payload(self, topic_branch):
        """Updates the SymErgion with no payload based on the topic branch.

        Args:
            topic_branch (str): the topic branch name.

        Raises:
            ValueError: if haven't found which task and feature branch
                        topic branch could be related with.
        """
        is_model = self.supported_coders and re.search(self.supported_coders, topic_branch)
        is_task = re.search(rf"^{self.supported_tasks}", topic_branch)

        # add model-feature branch
        if is_model and topic_branch not in self.ergon_branches:
            self._new_model_branch(topic_branch)

        # remove model-feature branch
        elif is_model and topic_branch in self.ergon_branches:
            self._delete_model_branch(topic_branch)

        # add not a symergion supported task branch
        elif not is_task and topic_branch not in self.branches:
            self.branches.append(topic_branch)

        # remove not a symergion supported task branch
        elif not is_task and topic_branch in self.branches:
            self.branches.remove(topic_branch)

        # add feature branch
        elif is_task and topic_branch not in self.ergon_branches:
            self._new_feature_branch(topic_branch)

        # remove feature branch
        elif is_task and topic_branch in self.feature_names:
            self._delete_feature_branch(topic_branch)

        else:
            raise ValueError(f"Unexpected {topic_branch} topic branch")

    def update(self, message):
        """Updates the SymErgion based on provided message.

        Args:
            message (dict): the message containing topic and payload.

        Raises:
            ValueError: if unable to identify action to be done.
        """
        topic_branch = message.get("topic")
        payload = message.get("payload")
        feature_match = topic_branch and re.search(self.feature_names_pattern, topic_branch)

        # request action on feature
        if not payload:
            self._update_with_no_payload(topic_branch)

        elif payload.get("note_message") and feature_match:
            feature_branch = feature_match.captures()
            ergons = [ergon for ergon in self.ergons if ergon.name in feature_branch]

            if len(ergons) == 0:
                return

            self._update_with_payload(payload, ergons.pop())

        elif payload.get("action") == "add":
            self._add_note(payload)

        elif payload.get("action") == "remove":
            self._remove_note(payload)

        else:
            raise ValueError(f"Unexpected payload value `{payload}`")
