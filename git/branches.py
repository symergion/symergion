import regex as re


class Branches(list):
    """A class to manage branches in a repository.
    """

    def __init__(self, repo, feature_branch=None):
        """Initialize the Branches class.

        Args:
            repo (Repo): The repository object.
            feature_branch (str): The name of the feature branch (optional).
        """
        super().__init__()

        self._repo = repo
        self._feature_branch = feature_branch

        if self.feature_branch:
            self.append(self.feature_branch)

    @property
    def feature_branch(self):
        """Get the feature branch name.

        Returns:
            str: The name of the feature branch.
        """
        return self._feature_branch

    @property
    def remotes(self):
        """Get a list of remote branches that match the feature branch pattern.

        Returns:
            list: A list of remote branches.
        """
        remote_branches = self.repo.remote_branches
        feature_branch = self.feature_branch if self.feature_branch else ""
        branch_pattern = fr"[\*\s]{'{2,2}'}+origin/([\p{'{L}'}\p{'{N}'}-_\.]*{feature_branch})\n"

        return re.findall(branch_pattern, remote_branches)

    @property
    def coders(self):
        """Get a list of branches excluding the feature branch.

        Returns:
            list: A list of branches excluding the feature branch.
        """
        return [branch for branch in self if branch != self.feature_branch]

    def append(self, branch, is_new=None):
        """Append a new branch to the list.

        Args:
            branch (str): The name of the branch to be added.
            is_new (bool): Whether the branch is new (optional).
        """
        if self.feature_branch:
            if is_new:
                self.repo.checkout(self.feature_branch)
                self.repo.create_branch(branch)

            self.repo.checkout(branch)

        super().append(branch)

    @property
    def repo(self):
        """Get the repository object.

        Returns:
            Repo: The repository object.
        """
        return self._repo

    def remove(self, branch):
        """Remove a branch from the list.

        Args:
            branch (str): The name of the branch to be removed.
        """
        if self.feature_branch:
            if branch == self.repo.current_branch:
                self.repo.checkout(self.repo.default_branch)

            if branch in self.remotes:
                self.repo.delete_remote_branch(branch)

            self.repo.delete_branch(branch)

        super().remove(branch)

    def clear(self):
        """Clear all branches from the list.
        """
        for branch in self.copy():
            self.remove(branch)
