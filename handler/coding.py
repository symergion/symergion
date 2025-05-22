import warnings
import regex as re

from handler.base import Handler
from utils.flatten import flatten
from utils.list import CustomList


class HandlerCoding(Handler):
    """HandlerCoding class responsible for handling coding-related events
    such as branch and note changes.

    Attributes:
        notes_pattern (str): pattern matching note and annotated object ids.

    Readonly Attributes:
        symergion (SymErgion): an instance of the Symergion class.
    """

    def __init__(self, symergion):
        """Initialize the HandlerCoding instance.

        Args:
            symergion (SymeErgionCoding): the SymErgion object.
        """
        super().__init__(symergion)
        self.notes_pattern = r"([0-9a-f]{40,40})\s([0-9a-f]{40,40})\n"

        self._handled = False
        self.sync_state()

    @property
    def local_branches(self):
        """Get a list of all local branches (including Ergon branches).

        Returns:
            CustomList: a CustomList of local branches.
        """
        return CustomList(set(self.symergion.branches) | set(self.symergion.ergon_branches))

    @property
    def remote_branches(self):
        """Get a list of all remote branches.

        Returns:
            CustomList: a CustomList of remote branches.
        """
        return CustomList(self.symergion.branches.remotes)

    @property
    def local_notes(self):
        """Get a list of all local notes (including Ergon notes).

        Returns:
            CustomList: a CustomList of local notes.
        """
        return CustomList(set(self.symergion.notes) | set(self.symergion.ergon_notes))

    @property
    def remote_notes(self):
        """Get a list of all remote notes using a regex pattern.

        Returns:
            CustomList: a CustomList of remote notes.
        """
        return CustomList(re.findall(self.notes_pattern, self.symergion.repo.notes))

    def dispatch(self, event):
        """Dispatch the appropriate method based on the event source path.

        Args:
            event: the event object containing information about the file change.
        """

        if event.src_path.endswith("logs/refs/notes"):
            print(f"The following event has happend:\n{event}")
            self._check_for_notes(event)

        elif event.src_path.endswith("logs/refs/heads"):
            print(f"The following event has happend:\n{event}")
            self._check_for_branches()

        if self._handled:
            print(f"Observing {self.symergion.repo.remote}/.git/logs/refs")
            self._handled = False

    def sync_state(self):
        """Synchronize the state by checking for branches and notes.
        Also, synchronize with Ergon commits.
        """
        print(f"{self.symergion} state is being synchronized with {self.symergion.repo} state.")
        self._check_for_branches()
        self._check_for_notes()

        for ergon in self.symergion.ergons:
            self.symergion.sync_with_commits(ergon)

        if self._handled:
            print(f"Observing {self.symergion.repo.remote}/.git/logs/refs")
            self._handled = False

    def _check_for_branches(self, event=None):
        """Check for differences in branches between local and remote repositories.
        Update the SymErgion object with branch changes.

        Args:
            event (DirModifiedEvent, optional): event that triggered check for branches.
        """
        removed_branches, added_branches = self._get_branches_diff()

        if event and (len(removed_branches) > 0 or len(added_branches) > 0):
            print(f"The following event has triggered branches change processing:\n{event}")

        elif not event:
            print("Branches change processing has been run directly, not triggered by any event.")

        for branch in removed_branches:
            # identify notes related with removed branch
            notes = self.symergion.notes + self.symergion.ergon_notes
            notes_to_remove = [n for n in notes if branch in self.symergion.repo.get_note_branches(n)]

            # process branch removal
            self.symergion.update({
                "topic": branch,
                "payload": None
            })

            # remove notes related with removed branch
            for removed_note in notes_to_remove:
                self._process_note(removed_note, "remove")

            self._handled = True

        for branch in added_branches:
            # process branch addition
            self.symergion.update({
                "topic": branch,
                "payload": None
            })

            self._handled = True

        # process added notes related with added branch
        added_ergon_branches = CustomList([b for b in self.symergion.ergon_branches if b in added_branches])
        added_notes = self.remote_notes - self.local_notes
        added_notes.sort(key=lambda n: self.symergion.repo.get_timestamp(n[1]))
        added_branches_notes = [n for n in added_notes if self.symergion.repo.get_note_branches(n) in added_ergon_branches]

        for note in added_branches_notes:
            self._process_note(note, "add")

    def _get_branches_diff(self):
        """Get the difference between local and remote branches.

        Returns:
            tuple: a tuple containing lists of removed and added branches.
        """
        removed_branches = self.local_branches - self.remote_branches
        added_branches = self.remote_branches - self.local_branches
        return removed_branches, added_branches

    def _check_for_notes(self, event=None):
        """Check for differences in notes between local and remote repositories.
        Update the Symergion object with note changes.

        Args:
            event (DirModifiedEvent, optional): event that triggered check for notes.
        """
        removed_notes = self.local_notes - self.remote_notes
        removed_notes.sort(key=lambda n: self.symergion.repo.get_timestamp(n[1]))

        added_notes = self.remote_notes - self.local_notes
        added_notes.sort(key=lambda n: self.symergion.repo.get_timestamp(n[1]))

        if event and (len(removed_notes) > 0 or len(added_notes) > 0):
            print(f"The following event has triggered notes change processing:\n{event}")

        elif not event:
            print("Notes change processing has been run directly, not triggered by any event.")

        for note in removed_notes:
            self._process_note(note, "remove")

        for note in added_notes:
            self._process_note(note, "add")

    def _process_note(self, note, action):
        """Process a note by splitting it into sub-notes and matching them with branches.
        Update the Symergion object with the processed note information.

        Args:
            note (tuple): the note to process.
            action (str): the action to perform ("add" or "remove").

        Raises:
            UserWarning:
                - if failed to resolve branch for note,
            ValueError:
                - if failed to split note by sub-notes,
                - if failed to resolve branch for sub-note
        """
        noted_branches = self.symergion.repo.get_note_branches(note)

        if len(noted_branches) < 1:
            warnings.warn(
                f"Can't resolve branch for note {note}, ensure it annotates supported task branch related commit",
                category=UserWarning,
                stacklevel=1
            )
            return

        # split note by task_branch pattern
        task_pattern = self.symergion.task_branch_spec
        pattern = re.compile(rf"((^|{task_pattern}).*?)(?={task_pattern}|$)", re.DOTALL)
        note_message = self.symergion.repo.get_note_message(note)
        sub_notes = [sn[0] for sn in pattern.findall(note_message) if sn[0]]

        # loop through sub notes match them with branches
        note_branches = [re.findall(task_pattern, sub_note) for sub_note in sub_notes]

        for index, sub_note in enumerate(sub_notes):
            noted_branch = None
            note_branch = note_branches[index]

            if len(note_branch) > 1:
                raise ValueError(f"Can't split by sub notes the note:\n{note_message}\n")

            if len(note_branch) == 0 and index > 0:
                raise ValueError(f"Can't resolve branch for sub note:\n{sub_note}\n")

            if len(note_branch) == index == 0 and noted_branches[0] not in flatten(note_branches):
                noted_branch = noted_branches.pop(0)

            elif len(note_branch) == 1 and note_branch[0] in noted_branches:
                noted_branch = noted_branches.pop(noted_branches.index(note_branch[0]))
                sub_note = re.split(f"{task_pattern}(?:[,;]?[\\s]*)", sub_note)[-1]

            else:
                raise ValueError(f"Can't resolve branch for sub note:\n{sub_note}\n")

            symergion_message = {
                "topic": noted_branch,
                "payload": {
                    "action": action,
                    "note": note,
                    "note_message": sub_note
                }
            }
            self.symergion.update(symergion_message)
            self._handled = True
