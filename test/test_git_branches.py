import unittest

import os
import shutil
import subprocess

from git.repository import Repo
from git.branches import Branches


class TestBranches(unittest.TestCase):
    """A test case for the Branches class.
    """

    def setUp(self):
        """Set up the test environment before each test method is executed.
            - Initializes a remote Git repository,
            - sets up user configuration,
            - creates a source file,
            - commits it,
            - sets up a feature branch,
            - initializes Repo object,
            - initializes Branches object.
        """
        self.remote_repo = "/test_repo"
        os.mkdir(self.remote_repo)
        self.default_branch = "main"
        subprocess.run(
            ["git", "-C", self.remote_repo, "init", "-b", self.default_branch, self.remote_repo],
            check=True
        )
        config = f"{self.remote_repo}/.git/config"
        subprocess.run(
            ["git", "-C", self.remote_repo, "config", "-f", config, "user.email", "test@localhost"],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.remote_repo, "config", "-f", config, "user.name", "Test User"],
            check=True
        )
        self.source_file = "test_source_file"
        with open(f"{self.remote_repo}/{self.source_file}", "w", encoding="utf-8") as f:
            f.write("test file content")
        subprocess.run(
            ["git", "-C", self.remote_repo, "add", self.source_file],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.remote_repo, "commit", "-m", "Initial commit"],
            check=True
        )
        self.feature_branch = "feature"
        subprocess.run(
            ["git", "-C", self.remote_repo, "branch", self.feature_branch],
            check=True
        )
        self.repo = Repo(self.remote_repo, self.default_branch)
        self.local_repo = self.repo.local
        self.branches = Branches(self.repo, self.feature_branch)

    def tearDown(self):
        """Clean up the test environment after each test method is executed.
        Removes the remote and local repositories to ensure a clean state for subsequent tests.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_init(self):
        """Test the initialization of the Branches class.
        Verifies that the Branches instance is created correctly and contains the expected branches.
        """
        self.assertIsInstance(self.branches, Branches)
        self.assertIsInstance(self.branches, list)
        self.assertEqual(self.branches, [self.feature_branch])
        self.assertIsInstance(self.branches.coders, list)
        self.assertNotIn(self.branches.feature_branch, self.branches.coders)

    def test_remotes(self):
        """Test the remotes property of the Branches class.
        Ensures that the feature branch is included in the list of remote branches.
        """
        self.assertIn(self.feature_branch, self.branches.remotes)

    def test_append_existing(self):
        """Test appending an existing branch to the Branches instance.
            - Creates a new branch locally,
            - appends it to the Branches instance,
            - verifies its presence.
        """
        existing_branch = f"{self.feature_branch}_existing_branch"
        subprocess.run(
            ["git", "-C", self.local_repo, "branch", existing_branch],
            check=True
        )
        self.branches.append(existing_branch)

        self.assertSetEqual(set(self.branches), {self.feature_branch, existing_branch})

    def test_append_new(self):
        """Test appending a new branch to the Branches instance.
            - Appends a new branch to the Branches instance with the `is_new` flag set to True,
            - verifies its presence.
        """
        new_branch = f"{self.feature_branch}_new_branch"
        self.branches.append(new_branch, is_new=True)

        self.assertSetEqual(set(self.branches), {self.feature_branch, new_branch})

    def test_remove(self):
        """Test removing a branch from the Branches instance.
            - Checks out the main branch,
            - removes the feature branch,
            - and verifies its absence.
        """
        self.repo.checkout("main")
        self.branches.remove(self.feature_branch)

        self.assertEqual(self.branches, [])
        self.assertNotIn(self.feature_branch, self.branches.remotes)

    def test_clear(self):
        """Test clearing all branches from the Branches instance.
            - Checks out the main branch,
            - clears all branches,
            - verifies that the list is empty.
        """
        self.repo.checkout("main")
        self.branches.clear()

        self.assertEqual(self.branches, [])
