import os
import shutil
import subprocess
import unittest
from unittest.mock import Mock, patch

import torch

from git.repository import Repo
from handler.coding import HandlerCoding
from symerg.coder import SymErgCoder
from symergion.coding import SymErgionCoding
from symergion.config import Config

from utils.setup_test import get_test_config, create_test_ergon


class TestHandlerCoding(unittest.TestCase):
    """This class tests the functionality of the HandlerCoding class,
    """

    def setUp(self):
        """Set up the test environment before each test method.
            - Initializes a test Git repository,
            - creates necessary configuration,
            - adds test source file,
            - instantiates coding Handler with SymErgion, SymErg and Ergon,
            - sets mock model and tokenizer for SymErg,
            - sets up mock events for testing.
        """
        handler_config, _ = get_test_config()
        self.config = Config(handler_config)
        remote_repo = "/test_repo"
        os.mkdir(remote_repo)
        subprocess.run(
            ["git", "-C", remote_repo, "init", "-b", self.config.default_branch, remote_repo],
            check=True
        )
        git_config = f"{remote_repo}/.git/config"
        subprocess.run(
            ["git", "-C", remote_repo, "config", "-f", git_config, "user.email", "test@localhost"],
            check=True
        )
        subprocess.run(
            ["git", "-C", remote_repo, "config", "-f", git_config, "user.name", "Test User"],
            check=True
        )
        self.source_file = "test_source_file"
        self.destination_file = "test_destination_file"
        with open(f"{remote_repo}/{self.source_file}", "w", encoding="utf-8") as f:
            f.write("test file content")
        subprocess.run(
            ["git", "-C", remote_repo, "add", self.source_file],
            check=True
        )
        subprocess.run(
            ["git", "-C", remote_repo, "commit", "-m", "Initial commit"],
            check=True
        )
        self.repo = Repo(remote_repo, "main")
        self.symergion = SymErgionCoding(self.repo, self.config)

        self.symerg_coder = SymErgCoder(self.config.checkpoints[0], 1, 10, 64)

        self.symerg_coder.model = Mock()
        self.symerg_coder.model.attach_mock(Config.from_json(f"{self.symerg_coder.name_or_path}/config.json"), "config")
        self.symerg_coder.model.attach_mock(lambda *args, **kwargs: torch.tensor([[1, 1, 1, 2, 2, 2]]), "generate")

        self.symerg_coder.tokenizer = Mock()
        self.symerg_coder.tokenizer.return_value = {"input_ids": torch.tensor([[1, 1, 1]])}
        self.symerg_coder.tokenizer.attach_mock(lambda *args, **kwargs: "mocked generated code", "decode")

        self.symergion.attach_symerg(self.symerg_coder)
        self.task_branch, self.ergon = create_test_ergon(self.repo, "TestCase_abc")
        self.symerg_coder.attach_ergon(self.ergon)

        self.handler = HandlerCoding(self.symergion)
        self.mock_notes_event = Mock()
        self.mock_notes_event.src_path = "logs/refs/notes"
        self.mock_branches_event = Mock()
        self.mock_branches_event.src_path = "logs/refs/heads"

        source_part = f"source: {self.source_file}"
        destination_part = f"destination: {self.destination_file}"
        user_prompt_part = "test initial note"
        self.init_message = f"{source_part} {destination_part} {user_prompt_part}"

    def tearDown(self):
        """Clean up the test environment after each test method.
        Removes the test Git repository and local repository directories.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_init(self):
        """Test the initialization of the HandlerCoding class.
            - Verifies that the HandlerCoding instance is initialized correctly,
            - calls the necessary methods to check for branches and notes.
        """
        self.assertEqual(self.handler.symergion, self.symergion)
        with patch.object(HandlerCoding, "_check_for_branches") as mock_check_for_branches:
            HandlerCoding(self.symergion)
            mock_check_for_branches.assert_called_once()
        with patch.object(HandlerCoding, "_check_for_notes") as mock_check_for_notes:
            HandlerCoding(self.symergion)
            mock_check_for_notes.assert_called_once()

    def test_dispatch_supported_task_model_branch(self):
        """Test the dispatch method for a supported task model branch.
            - Adds an initial note to the task branch,
            - creates a model branch,
            - dispatches the event,
            - verifies that it is added to the correct list of branches.
        """
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "add", "-m", self.init_message, self.task_branch],
            check=True
        )
        model_branch = f"model_{self.task_branch}"
        subprocess.run(
            ["git", "-C", self.repo.remote, "branch", model_branch],
            check=True
        )
        self.assertNotIn(model_branch, self.symergion.branches + self.symergion.ergon_branches)
        self.handler.dispatch(self.mock_branches_event)

        self.assertNotIn(model_branch, self.symergion.branches)
        self.assertIn(model_branch, self.symergion.ergon_branches)

    def test_dispatch_supported_task_branch(self):
        """Test the dispatch method for a supported task branch.
            - Creates a supported task branch,
            - verifies that it is not in the list of branches
            - dispatches the event,
            - verifies that it is added to the correct list of branches.
        """
        branch = "TestCase_def"
        subprocess.run(
            ["git", "-C", self.repo.remote, "branch", branch],
            check=True
        )
        self.assertNotIn(branch, self.symergion.branches + self.symergion.ergon_branches)
        self.handler.dispatch(self.mock_branches_event)

        self.assertNotIn(branch, self.symergion.branches)
        self.assertIn(branch, self.symergion.ergon_branches)

    def test_dispatch_non_supported_task_branch(self):
        """Test the dispatch method for a non-supported task branch.
            - Creates a non-supported task branch,
            - verifies that it is not in the list of branches,
            - dispatches the event,
            - verifies that it is not in the list of branches.
        """
        branch = "non_supported_task_branch"
        subprocess.run(
            ["git", "-C", self.repo.remote, "branch", branch],
            check=True
        )

        self.assertNotIn(branch, self.symergion.branches + self.symergion.ergon_branches)
        self.handler.dispatch(self.mock_branches_event)
        self.assertNotIn(branch, self.symergion.ergon_branches)
        self.assertIn(branch, self.symergion.branches)

    def test_dispatch_initial_note(self):
        """Test the dispatch method for an initial note.
            - Adds an initial note,
            - dispatches the event,
            - verifies that the note is correctly processed and stored.
        """
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "add", "-m", self.init_message],
            check=True
        )
        self.handler.dispatch(self.mock_notes_event)
        self.assertEqual(len(self.symergion.ergon_notes), 1)

        written_note = subprocess.run(
            ["git", "-C", self.repo.remote, "show", self.symergion.ergon_notes[-1][0]],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(written_note.stdout.removesuffix("\n"), self.init_message)

    def test_dispatch_remove_note(self):
        """Test the dispatch method for removing a note.
            - Adds an initial note,
            - dispatches the event,
            - adds an additional note,
            - dispatches the event,
            - removes the last note,
            - verifies that the note is correctly removed.
        """
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "add", "-m", self.init_message, self.task_branch],
            check=True
        )
        self.handler.dispatch(self.mock_notes_event)
        additional_message = "additional_note"
        symerg_name = os.path.basename(self.config.checkpoints[0].get('name_or_path'))
        model_branch = f"{symerg_name}_{self.task_branch}"
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "add", "-m", additional_message, model_branch],
            check=True
        )
        self.handler.dispatch(self.mock_notes_event)

        last_note = self.symergion.ergon_notes[-1]
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "remove", last_note[1]],
            check=True
        )
        self.handler.dispatch(self.mock_notes_event)
        self.assertNotIn(last_note, self.symergion.ergon_notes)
