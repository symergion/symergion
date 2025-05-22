import os
import shutil
import subprocess
import unittest
from unittest.mock import Mock, patch

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from git.repository import Repo
from git.branches import Branches
from symergion.coding import SymErgionCoding
from symergion.config import Config
from symerg.coder import SymErgCoder
from ergon.code import ErgonCode
from utils.setup_test import get_test_config, create_test_ergon
from utils.flatten import flatten


class TestSymErgionCoding(unittest.TestCase):
    """A test case for the SymErgionCoding class.
    Verifies the functionality of the SymErgionCoding class, including:
        - its initialization,
        - command execution,
        - instantiation of symers and ergons,
        - decommissioning of ergons,
        - updating tasks.
    """

    def setUp(self):
        """Set up the test environment before each test method is run.
            - initializes the configuration,
            - creates a temporary remote repository,
            - sets up Git configuration with test source file,
            - initializes various objects needed for testing.
        """
        config_json, _ = get_test_config()
        self.config = Config(config_json)
        remote_repo = "/test_repo"
        os.mkdir(remote_repo)
        default_branch = "main"
        subprocess.run(
            ["git", "-C", remote_repo, "init", "-b", default_branch, remote_repo],
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
        source_file = "test_source_file"
        with open(f"{remote_repo}/{source_file}", "w", encoding="utf-8") as f:
            f.write("test file content")
        subprocess.run(
            ["git", "-C", remote_repo, "add", source_file],
            check=True
        )
        subprocess.run(
            ["git", "-C", remote_repo, "commit", "-m", "Initial commit"],
            check=True
        )
        destination_file = "test_destination_file"
        self.init_message = f"destination: {destination_file}\nsource: {source_file}"
        self.repo = Repo(remote_repo, "main")
        self.symergion = SymErgionCoding(self.repo, self.config)
        self.symerg_coder = SymErgCoder(self.config.checkpoints[0], 1, 10, 64)
        self.branch, self.ergon = {}, {}
        self.branch[1], _ = create_test_ergon(self.repo, "TestCase_abc")
        self.branch[2], _ = create_test_ergon(self.repo, "TestCase_def")
        self.branch[3], self.ergon[3] = create_test_ergon(self.repo, "TestCase_ijk")
        self.branch[4], self.ergon[4] = create_test_ergon(self.repo, "TestCase_lmn")
        self.branch[5], self.ergon[5] = create_test_ergon(self.repo, "TestCase_opq")

        self.model = Mock("config")
        self.model.config = Config.from_json(f"{self.symerg_coder.name_or_path}/config.json")
        self.model.attach_mock(lambda *args, **kwargs: None, "eval")
        self.model.attach_mock(lambda *args, **kwargs: torch.tensor([[1, 1, 2, 2]]), "generate")

        self.tokenizer = Mock()
        self.tokenizer.return_value = {"input_ids": torch.tensor([[1, 1]])}
        self.tokenizer.attach_mock(lambda *args, **kwargs: "mocked generated code", "decode")

    def tearDown(self):
        """Clean up the test environment after each test method is run.
        This method removes the temporary remote and local repositories created during the setup.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_init(self):
        """Test the initialization of the SymErgionCoding instance.
        This test checks that the SymErgionCoding instance is properly
        initialized with the expected attributes.
        """
        templates_tasks = [f"({k})" for k in self.config.templates]

        self.assertIsInstance(self.symergion.symergs, list)
        self.assertIsInstance(self.symergion.coders, list)
        self.assertIsInstance(self.symergion.reasoners, list)
        self.assertIsInstance(self.symergion.ergons, list)
        self.assertListEqual(self.symergion.supported_tasks.split("|"), templates_tasks)
        self.assertIsNone(self.symergion.supported_coders)
        self.assertIsInstance(self.symergion.repo, Repo)
        self.assertEqual(self.symergion.repo.remote, self.repo.remote)
        self.assertEqual(self.symergion.repo.default_branch, "main")
        self.assertEqual(self.symergion.repo.local, self.repo.local)

        current_branch = subprocess.run(
            ["git", "-C", self.repo.local, "branch"],
            capture_output=True,
            text=True,
            check=True
        )
        ergon_branches = flatten([e.branches for e in self.symergion.ergons])

        self.assertIn(self.symergion.repo.default_branch, current_branch.stdout)
        self.assertIsInstance(self.symergion.branches, Branches)
        self.assertEqual(self.symergion.ergon_branches, ergon_branches)
        self.assertIsInstance(self.symergion.notes, list)
        self.assertEqual(self.symergion.notes, self.symergion._notes)

    def test_run_command_success(self):
        """Test the successful execution of a Git command.
        This test verifies that the `run_command` method of the Repo class
        executes a Git command successfully.
        """
        status = Repo.run_command(["git", "-C", self.repo.local, "status"]).stdout

        self.assertIn("On branch", status)

    def test_run_command_failure(self):
        """Test the failure of a Git command execution.
        This test checks that the `run_command` method
        raises a ValueError when executing an invalid Git command.
        """
        error_msg = "`git -C test_repo grep` caused the following error: fatal: no pattern given"
        with self.assertRaises(ValueError, msg=error_msg):
            incorrect_command = ["git", "-C", self.repo.local, "grep"]
            self.assertIn("On branch", Repo.run_command(incorrect_command).stdout)

    def test_instantiate_symerg(self):
        """Test the instantiation of a SymErgCoder object.
        This test verifies that the `instantiate_symerg` method
        correctly creates a SymErgCoder object and
        attaches it to the SymErgionCoding instance.
        """
        symerg = self.symergion.instantiate_symerg(self.config.checkpoints[0])
        name_or_path = self.config.checkpoints[0].get("name_or_path")

        self.assertIsInstance(symerg, SymErgCoder)
        self.assertEqual(symerg.name_or_path, name_or_path)
        self.symergion.attach_symerg(symerg)
        self.assertIn(os.path.basename(name_or_path), self.symergion.supported_coders)

    def test_instantiate_ergon(self):
        """Test the instantiation of an ErgonCode object.
        This test verifies that the `instantiate_ergon` method correctly
        creates an ErgonCode object with the specified name.
        """
        ergon = self.symergion.instantiate_ergon(
            name=self.branch[1]
        )

        self.assertIsInstance(ergon, ErgonCode)
        self.assertEqual(ergon.name, self.branch[1])
        self.assertEqual(ergon.branches.repo.local, self.repo.local)

    def test_decomission_ergon(self):
        """Test the decommissioning of an ErgonCode object.
        This test verifies that the `decomission_ergon` method correctly
        removes an ErgonCode object from the SymErgionCoding instance's ergons list.
        """
        ergon = self.symergion.instantiate_ergon(
            name=self.branch[1]
        )
        self.symergion.decomission_ergon(ergon)

        self.assertNotIn(ergon, self.symergion.ergons)

    def test_update_new_task(self):
        """Test the update of a new task.
        This test verifies that the `update` method correctly
        adds a new ErgonCode object to the SymErgionCoding instance's ergons list
        when a new task is received.
        """
        self.symergion.attach_symerg(self.symerg_coder)
        message = {
            "topic": self.branch[2],
            "payload": None
        }
        self.symergion.update(message)

        self.assertIsInstance(self.symergion.ergons[-1], ErgonCode)
        self.assertEqual(self.symergion.ergons[-1].name, self.branch[2])

    def test_update_delete_model_branch(self):
        """Test the deletion of a model branch.
        This test verifies that the `update` method correctly
        deletes a model branch when a delete message is received.
        """
        self.symergion.attach_symerg(self.symerg_coder)
        model = os.path.basename(self.symerg_coder.name_or_path)
        topic_branch = f"{model}_{self.branch[3]}"
        self.symergion.branches.append(topic_branch)
        self.symerg_coder.update({"topic": topic_branch, "payload": self.ergon[3]})
        self.ergon[3].branches.append(topic_branch, is_new=True)
        message = {
            "topic": topic_branch,
            "payload": None
        }
        self.symergion.update(message)
        output = subprocess.run(
            ["git", "-C", self.repo.local, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertNotIn(topic_branch, output.stdout)

    def test_update_delete_feature_branch(self):
        """Test the deletion of a feature branch.
        This test verifies that the `update` method correctly
        deletes a feature branch when a delete message is received.
        """
        self.symergion.attach_symerg(self.symerg_coder)
        topic_branch = self.branch[4]
        self.symergion.branches.append(topic_branch)
        self.symerg_coder.update({"topic": topic_branch, "payload": self.ergon[4]})
        message = {
            "topic": topic_branch,
            "payload": None
        }
        self.symergion.update(message)
        output = subprocess.run(
            ["git", "-C", self.repo.local, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertNotIn(topic_branch, output.stdout)

    def test_update_generate(self):
        """Test the generation of code based on a note.
        This test verifies that the `update` method correctly
        generates code based on a note when a generate message is received.
        """
        self.symergion.attach_symerg(self.symerg_coder)
        new_task = {
            "topic": self.branch[5],
            "payload": self.ergon[5]
        }
        self.symergion._notify(new_task)
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "add", "-m", self.init_message, self.branch[5]],
            capture_output=True,
            text=True,
            check=True
        )
        notes = subprocess.run(
            ["git", "-C", self.repo.remote, "notes"],
            capture_output=True,
            text=True,
            check=True
        )
        init_note = tuple(notes.stdout.split())
        init_generate = {
            "topic": self.branch[5],
            "payload": {
                "action": "add",
                "note": init_note,
                "note_message": self.init_message
            }
        }
        with patch.object(AutoTokenizer, "from_pretrained") as pretrained_tokenizer, \
                patch.object(AutoModelForCausalLM, "from_pretrained") as pretrained_model:
            pretrained_tokenizer.return_value = self.tokenizer
            pretrained_model.return_value = self.model

            self.symergion.update(init_generate)

        test_message = "test"
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "add", "-m", test_message, f"{os.path.basename(self.symerg_coder.name_or_path)}_{self.branch[5]}"],
            check=True
        )
        notes = subprocess.run(
            ["git", "-C", self.repo.remote, "notes"],
            capture_output=True,
            text=True,
            check=True
        )
        test_note = tuple(notes.stdout.split())
        generate = {
            "topic": self.branch[5],
            "payload": {
                "note": test_note,
                "note_message": test_message
            }
        }
        self.symergion.update(generate)
        subprocess.run(
            ["git", "-C", self.repo.remote, "notes", "remove", test_note[1]],
            check=True
        )
        task_branch = self.branch[5]
        symerg_branch = f"{os.path.basename(self.symerg_coder.name_or_path)}_{self.branch[5]}"
        revisions = f"{task_branch}..{symerg_branch}"
        output = subprocess.run(
            ["git", "-C", self.repo.local, "log", "--oneline", revisions],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn(test_message, output.stdout)
