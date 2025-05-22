import subprocess
import regex as re

from utils.list import CustomList


class Repo():
    """A class to manage git repository.
    """
    def __init__(self, remote_repo, default_branch):
        """Initialize a new Repo instance.

        Args:
            remote_repo (str): The URL or path of the remote repository.
            default_branch (str): The default branch name (main or master).
        """
        self._remote = remote_repo

        # Configure safe directory settings
        config = ["git", "config", "--global", "--add", "safe.directory"]
        self.run_command(config + [self.remote])
        self.run_command(config + [f"{self.remote}/.git"])

        self._default_branch = default_branch
        self._branch_pattern = r"[\*\s]{2,2}([\p{L}\p{N}-_\.]*)(?:\n|$)"

        # Clone the repository
        clone = ["git", "clone", "-b", self.default_branch, self.remote]
        git_clone = self.run_command(clone)

        repo_name_pattern = r"Cloning into '([\p{L}\p{N}_\-\.]+)'...\ndone.\n"
        [self._local] = re.findall(repo_name_pattern, git_clone.stderr)

    @property
    def remote(self):
        """Get the remote repository URL or path.

        Returns:
            str: Remote repository URL or path.
        """
        return self._remote

    @property
    def local(self):
        """Get the local repository path.

        Returns:
            str: Local repository path.
        """
        return self._local

    @property
    def branch_pattern(self):
        """Get the branch pattern used for matching branches.

        Returns:
            str: Branch pattern.
        """
        return self._branch_pattern

    @property
    def default_branch(self):
        """Get the default branch of the repository.

        Returns:
            str: Default branch name.
        """
        return self._default_branch

    @property
    def current_branch(self):
        """Get the current branch of the local repository.

        Returns:
            str: Current branch name.
        """
        status = ["git", "-C", self.local, "status", "-sb"]
        git_status = self.run_command(status).stdout

        pattern = r"^##\s*([\p{L}\p{N}-_/]+[\.]?[\p{L}\p{N}-_/]+)(?:\s*...origin/[\p{L}\p{N}-_\./]+)?"
        [current_branch] = re.findall(pattern, git_status)
        return current_branch

    @property
    def remote_branches(self):
        """Get all remote branches of the repository.

        Returns:
            list: List of remote branches.
        """
        self._pull()
        branch = ["git", "-C", self.local, "branch", "--remotes", "--sort=committerdate"]
        git_branch = self.run_command(branch)
        remote_branches = git_branch.stdout
        return remote_branches

    @property
    def notes(self):
        """Get all notes associated with the repository.

        Returns:
            str: Notes output.
        """
        self._prune_remote()
        self._prune_remote_notes()
        notes = ["git", "-C", self.remote, "notes", "list"]
        git_notes = self.run_command(notes)
        return git_notes.stdout

    @classmethod
    def run_command(cls, command):
        """Run a Git command and handle errors.

        Args:
            command (list): List of command arguments.

        Returns:
            CompletedProcess: CompletedProcess instance
        """
        git_command = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )

        if re.search(r"^fatal: [\s\S]+", git_command.stderr):
            raise ValueError(f"`{' '.join(command)}` caused the error:\n {git_command.stderr}\n")

        return git_command

    def get_note_branches(self, note):
        """Get branches associated with a specific note.

        Args:
            note (tuple): Note object.

        Returns:
            list: List of branch names.
        """
        noted_object = note[1]

        if not re.search(self.branch_pattern, self.get_object_branches(noted_object)):
            return []

        note_branches = re.findall(self.branch_pattern, self.get_object_branches(noted_object))

        if len(note_branches) > 1:
            merged_branches = self.get_object_branches(noted_object, merged=True)
            note_branches = re.findall(self.branch_pattern, merged_branches)

        if len(note_branches) > 0 and self.default_branch in note_branches:
            note_branches.remove(self.default_branch)

        if len(note_branches) > 1:
            sorted_branches = self.run_command(["ls", "-xtr1", f"{self.remote}/.git/refs/heads"])
            sorted_branches_list = [b for b in sorted_branches.stdout.split("\n") if b]
            note_branches = sorted(note_branches, key=sorted_branches_list.index)

        return CustomList(note_branches)

    def get_note_message(self, note):
        """Get the message associated with a specific note.

        Args:
            note (tuple): Note object.

        Returns:
            str: Note message.
        """
        noted_object = note[1]
        show_object = ["git", "-C", self.remote, "notes", "show", noted_object]
        show_object_output = self.run_command(show_object)

        if show_object_output.returncode == 0:
            return show_object_output.stdout.removesuffix("\n")

        return self.get_object(note[0])

    def get_object(self, git_object):
        """Get the content of a specific Git object.

        Args:
            git_object: Git object identifier.

        Returns:
            str: Content of the Git object.
        """
        show_object = ["git", "-C", self.remote, "show", git_object]
        show_object_output = self.run_command(show_object)
        git_object_value = show_object_output.stdout.removesuffix("\n")
        return git_object_value

    def object_exists(self, commit_object):
        """Check if a specific Git object exists.

        Args:
            commit_object: Git object identifier.

        Returns:
            bool: True if the object exists, False otherwise.
        """
        cat_file_process = subprocess.run(
            ["git", "-C", self.local, "cat-file", "-e", commit_object],
            check=False
        )
        return not cat_file_process.returncode

    def get_object_branches(self, git_object, merged=False):
        """Get branches containing a specific Git object.

        Args:
            git_object: Git object identifier.
            merged (bool, optional): Whether to include only merged branches.

        Returns:
            str: Branches containing the Git object.
        """
        self._pull()
        branch = ["git", "-C", self.local, "branch", "--contains", git_object]
        if merged:
            branch.extend(["--merged", git_object])
        git_branch = self.run_command(branch)
        object_branches = git_branch.stdout
        return object_branches

    def get_timestamp(self, commit_object):
        """Get the timestamp of a specific commit object.

        Agrs:
            commit_object: Commit object identifier.

        Returns:
            Timestamp of the commit object.
        """
        if not self.object_exists(commit_object):
            return .0

        show = ["git", "-C", self.local, "show", "-s", '--format="%ct"', commit_object]
        show_timestamp = self.run_command(show)
        return float(show_timestamp.stdout.strip(' \n"'))

    def get_ergon_branch_messages(self, branch):
        """Get commit messages for git objects
            starting from the commit branch points to,
            including objects belonging to all branches.

        Args:
            branch (str): branch for which messages should be searched.

        Returns:
            list: List of commit messages.
        """
        log = ["git", "-C", self.remote, "log", "--pretty=format:%B%x00", "--branches", f"{branch}.."]
        git_log = self.run_command(log)
        response = git_log.stdout
        messages = [message.strip("\n ") for message in response.split("\0")]
        return [message for message in messages if len(message) > 0]

    def get_objects_messages(self, objects):
        """Get commit messages for a list of Git objects.

        Args:
            objects (list): List of Git object identifiers.

        Returns:
            list: List of commit messages.
        """
        log = ["git", "-C", self.remote, "log", "--pretty=format:%B%x00", objects, "--"]
        git_log = self.run_command(log)
        response = git_log.stdout
        messages = [message.strip("\n ") for message in response.split("\0")]
        return [message for message in messages if len(message) > 0]

    def create_branch(self, branch):
        """Create a new branch in the repository.

        Args:
            branch (str): Name of the new branch.
        """
        git_branch = ["git", "-C", self.local, "branch", branch]
        self.run_command(git_branch)
        set_upstream = ["git", "-C", self.local, "push", "--set-upstream", "origin", branch]
        self.run_command(set_upstream)

    def delete_branch(self, branch):
        """Delete a branch from the repository.

        Args:
            branch (str): Name of the branch to delete.
        """
        branch = ["git", "-C", self.local, "branch", "-D", branch]
        self.run_command(branch)

    def delete_remote_branch(self, branch):
        """Delete a remote branch from the repository.

        Args:
            branch (str): Name of the remote branch to delete.
        """
        push_origin = ["git", "-C", self.local, "push", "origin", "--delete", branch]
        self.run_command(push_origin)

    def checkout(self, branch):
        """Checkout a specific branch in the repository.

        Args:
            branch (str): Name of the branch to checkout.
        """
        self._pull()
        checkout = ["git", "-C", self.local, "checkout", branch, "--"]
        git_checkout = self.run_command(checkout)
        print(git_checkout.stderr)

    def add(self, destination_file):
        """Add a file to the staging area.

        Args:
            destination_file (str): Path of the file to add.
        """
        git_add = ["git", "-C", self.local, "add", destination_file]
        self.run_command(git_add)

    def commit(self, comment):
        """Commit changes with a specified message.

        Args:
            comment (str): Commit message.
        """
        commit = ["git", "-C", self.local, "commit", "-m", comment]
        self.run_command(commit)
        self._push()

    def set_user(self, name):
        """Set the user name and email for Git operations.

        Args:
            name (str): User name.
        """
        config_email = ["git", "-C", self.local, "config", "user.email", f"{name}@localhost"]
        self.run_command(config_email)
        config_user = ["git", "-C", self.local, "config", "user.name", f"{name}"]
        self.run_command(config_user)

    def _pull(self):
        """Pull the latest changes from the remote repository.
        """
        self._prune_remote()
        pull = ["git", "-C", self.local, "pull", "--prune"]
        self.run_command(pull)

    def _push(self):
        """Push the changes to the remote repository.
        """
        push = ["git", "-C", self.local, "push"]
        self.run_command(push)
        self._prune_remote()

    def _prune_remote(self):
        """Prune stale remote-tracking references.
        """
        prune = ["git", "-C", self.remote, "prune"]
        self.run_command(prune)

    def _prune_remote_notes(self):
        """Prune stale notes from the remote repository.
        """
        prune = ["git", "-C", self.remote, "notes", "prune"]
        self.run_command(prune)
