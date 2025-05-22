import unittest

import os
import shutil
import subprocess
import regex as re

from utils import capture_output
from git.repository import Repo


class TestRepo(unittest.TestCase):
    """A test class for the `Repo`.
    """

    def setUp(self):
        """Set up the test environment.
        Creates a new Git repository with:
            - initial commit,
            - default and feature branches,
            - source code file,
            - note.
        Creates Repo object.
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
        self.local_repo = "test_repo"
        self.feature_branch = "feature"
        subprocess.run(
            ["git", "-C", self.remote_repo, "branch", self.feature_branch],
            check=True
        )
        self.test_message = "Test note"
        subprocess.run(
            ["git", "-C", self.remote_repo, "notes", "add", "-m", self.test_message, self.default_branch],
            check=True
        )
        notes = subprocess.run(
            ["git", "-C", self.remote_repo, "notes", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        note_ids_pattern = r"([abcdef\p{N}]{40,40})\s([abcdef\p{N}]{40,40})\n"
        [self.test_note] = re.findall(note_ids_pattern, notes.stdout)
        self.repo = Repo(self.remote_repo, self.default_branch)

    def tearDown(self):
        """Clean up the test environment by removing the created Git repositories.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_init(self):
        """Test the initialization of the `Repo` object.
        """
        self.assertIsInstance(self.repo, Repo)
        self.assertEqual(self.remote_repo, self.repo.remote)
        self.assertEqual(self.local_repo, self.repo.local)
        self.assertEqual(self.default_branch, self.repo.default_branch)

    def test_current_branch(self):
        """Test the retrieval of the current branch.
        """
        self.assertEqual(self.default_branch, self.repo.current_branch)

    def test_remote_branches(self):
        """Test the retrieval of remote branches.
        """
        self.assertIn(self.feature_branch, self.repo.remote_branches)

    def test_get_note_message(self):
        """Test the retrieval of a note message.
        """
        self.assertEqual(self.test_message, self.repo.get_note_message(self.test_note))

    def test_get_note_branch(self):
        """Test the retrieval of a note branch.
        """
        self.assertEqual([], self.repo.get_note_branches(self.test_note))

    def test_get_timestamp(self):
        """Test the retrieval of a branch timestamp.
        """
        branch_timestamp = self.repo.get_timestamp(self.default_branch)

        self.assertIsInstance(branch_timestamp, float)
        self.assertGreater(branch_timestamp, 0.0)

    def test_get_objects_messages(self):
        """Test the retrieval of commit messages for a branch.
        """
        self.assertEqual(["Initial commit"], self.repo.get_objects_messages(self.default_branch))

    def test_create_branch(self):
        """Test the creation of a new branch.
        """
        branch = "created_branch"
        self.repo.create_branch(branch)
        git_branches = subprocess.run(
            ["git", "-C", self.local_repo, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn(branch, git_branches.stdout)

    def test_delete_branch(self):
        """Test the deletion of a local branch.
        """
        branch_to_delete = "branch_to_delete"
        subprocess.run(
            ["git", "-C", self.local_repo, "branch", branch_to_delete],
            check=True
        )
        self.repo.delete_branch(branch_to_delete)
        git_branches = subprocess.run(
            ["git", "-C", self.local_repo, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertNotIn(branch_to_delete, git_branches.stdout)

    def test_delete_remote_branch(self):
        """Test the deletion of a remote branch.
        """
        branch_to_delete = "branch_to_delete"
        subprocess.run(
            ["git", "-C", self.remote_repo, "branch", branch_to_delete],
            check=True
        )
        self.repo.delete_remote_branch(branch_to_delete)
        git_branches = subprocess.run(
            ["git", "-C", self.remote_repo, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertNotIn(branch_to_delete, git_branches.stdout)

    def test_checkout(self):
        """Test the checkout of a branch.
        """
        checkout_output = capture_output(self.repo.checkout, self.feature_branch)

        self.assertIn(self.feature_branch, checkout_output)

    def test_add(self):
        """Test the addition of a file to the staging area.
        """
        source_file_path = os.path.join(self.local_repo, self.source_file)
        file_to_add = "test_add.txt"
        file_to_add_path = os.path.join(self.local_repo, file_to_add)
        subprocess.run(
            ["cp", source_file_path, file_to_add_path],
            check=True
        )
        self.repo.add(file_to_add)

        self.assertEqual(os.path.exists(os.path.join(self.local_repo, file_to_add)), True)

    def test_commit(self):
        """Test the committing of changes with a specific author.
        """
        source_file_path = os.path.join(self.local_repo, self.source_file)
        file_to_add = "test_commit.txt"
        file_to_add_path = os.path.join(self.local_repo, file_to_add)
        subprocess.run(
            ["cp", source_file_path, file_to_add_path],
            check=True
        )
        self.repo.add(file_to_add)
        self.repo.set_user("test")
        self.repo.commit(file_to_add)
        log = subprocess.run(
            ["git", "-C", self.local_repo, "log", "--oneline", "-1"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn(file_to_add, log.stdout)

    def test_set_user(self):
        """Test the setting of the user information.
        """
        self.repo.set_user("test")
        get_user_email = subprocess.run(
            ["git", "-C", self.local_repo, "config", "--get", "user.email"],
            capture_output=True,
            text=True,
            check=True
        )
        get_user_name = subprocess.run(
            ["git", "-C", self.local_repo, "config", "--get", "user.name"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn("test@localhost", get_user_email.stdout)
        self.assertIn("test", get_user_name.stdout)
