import os
import shutil
import subprocess
import unittest
from unittest.mock import Mock, patch

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from symergion.config import Config
from git.repository import Repo
from symerg.coder import SymErgCoder
from ergon.code import ErgonCode
from utils.setup_test import create_test_ergon


class TestSymErgCoder(unittest.TestCase):
    """This class tests the functionality of the SymErgCoder class,
    including:
        - generating code,
        - notifying ergons,
        - updating tasks,
        - handling branches.
    """

    def setUp(self):
        """Set up the test environment before each test method is executed.
            - Initializes the SymErgCoder instance,
            - sets up a remote Git repository,
            - creates test files,
            - initializes ErgonCode instances.
        """
        self.checkpoint = {
            "name_or_path": "/test/model",
            "trait": "coding"
        }
        self.symerg_coder = SymErgCoder(self.checkpoint, 1, 10, 64)

        remote_repo = "/test_repo"
        os.mkdir(remote_repo)
        default_branch = "main"
        subprocess.run(
            ["git", "-C", remote_repo, "init", "-b", default_branch, remote_repo],
            check=True
        )

        config = f"{remote_repo}/.git/config"
        test_email = "test@localhost"
        test_name = "Test User"
        subprocess.run(
            ["git", "-C", remote_repo, "config", "-f", config, "user.email", test_email],
            check=True
        )
        subprocess.run(
            ["git", "-C", remote_repo, "config", "-f", config, "user.name", test_name],
            check=True
        )

        self.source_file = "test_source_file"
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

        self.repo = Repo(remote_repo, default_branch)
        self.destination_file = "test_destination_file"

        self.branch, self.ergon = {}, {}
        self.branch[1], self.ergon[1] = create_test_ergon(self.repo, "TestCase_abcd")
        self.branch[2], self.ergon[2] = create_test_ergon(self.repo, "TestCase_efgh")
        self.branch[3], self.ergon[3] = create_test_ergon(self.repo, "TestCase_ijkl")
        self.branch[4], self.ergon[4] = create_test_ergon(self.repo, "TestCase_mnop")
        self.branch[5], self.ergon[5] = create_test_ergon(self.repo, "TestCase_qrst")
        self.branch[6], self.ergon[6] = create_test_ergon(self.repo, "TestCase_uvwx")

        self.model = Mock("config")
        self.model.config = Config.from_json(f"{self.symerg_coder.name_or_path}/config.json")
        self.model.attach_mock(lambda *args, **kwargs: None, "eval")
        self.model.attach_mock(lambda *args, **kwargs: torch.tensor([[1, 1, 2, 2]]), "generate")

        self.tokenizer = Mock()
        self.tokenizer.return_value = {"input_ids": torch.tensor([[1, 1]])}
        self.tokenizer.attach_mock(lambda *args, **kwargs: "mocked generated code", "decode")
        AutoTokenizer = Mock()
        AutoTokenizer.attach_mock(lambda *args, **kwargs: self.tokenizer, "from_pretrained")

    def tearDown(self):
        """Clean up the test environment after each test method is executed.
        Removes the remote and local repositories to ensure a clean state for the next test.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_code(self):
        """Test the generate method of SymErgCoder.
        Asserts that the generated response contains the test prompt.
        """
        prompt = "test"
        with patch.object(AutoTokenizer, "from_pretrained") as pretrained_tokenizer, \
                patch.object(AutoModelForCausalLM, "from_pretrained") as pretrained_model:
            pretrained_tokenizer.return_value = self.tokenizer
            pretrained_model.return_value = self.model

            response = self.symerg_coder.generate(prompt)

        self.assertTrue(torch.tensor([2]) in response)

    def test_notify_all_ergons(self):
        """Test the notify method of SymErgCoder when notifying all attached ergons.
        Asserts that the notification message is included in the commit history
        of the relevant branch.
        """
        model = os.path.basename(self.checkpoint.get("name_or_path"))
        self.symerg_coder.attach_ergon(self.ergon[1])
        topic_branch = f"{self.branch[1]}_{model}"
        self.ergon[1].prompt = f"destination: {self.destination_file}, source: {self.source_file}"
        note = "test notify all ergons"
        message = {
            "topic": topic_branch,
            "payload": note,
            "comment": note
        }
        self.symerg_coder._notify(message)
        output = subprocess.run(
            ["git", "-C", self.repo.local, "log", "--oneline", f"{self.branch[1]}..{topic_branch}"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn(note, output.stdout)

    def test_notify_specific_ergon(self):
        """Test the notify method of SymErgCoder when notifying a specific ergon.
        Asserts that the notification message is included in the commit history
        of the relevant branch.
        """
        model = os.path.basename(self.checkpoint.get("name_or_path"))
        self.symerg_coder.attach_ergon(self.ergon[2])
        topic_branch = f"{self.branch[2]}_{model}"
        self.ergon[2].prompt = f"destination: {self.destination_file}, source: {self.source_file}"
        note = "test notify one ergon"
        message = {
            "topic": topic_branch,
            "payload": note,
            "comment": note
        }
        self.symerg_coder._notify(message, self.ergon[2])
        output = subprocess.run(
            ["git", "-C", self.repo.local, "log", "--oneline", f"{self.branch[2]}..{topic_branch}"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn(note, output.stdout)

    def test_update_new_task_delete_task(self):
        """Test the update method of SymErgCoder for adding and deleting a new task.
        Asserts that the new task is added correctly and then removed from the list of ergons.
        """
        message = {
            "topic": self.branch[3],
            "payload": self.ergon[3]
        }
        self.symerg_coder.update(message)

        self.assertIsInstance(self.symerg_coder.ergons[-1], ErgonCode)
        self.assertEqual(self.symerg_coder.ergons[-1].name, self.branch[3])
        self.assertEqual(self.symerg_coder.ergons[-1].repo.local, self.repo.local)

        self.symerg_coder.update(message)

        self.assertNotIn(self.ergon[3], self.symerg_coder.ergons)

    def test_update_add_model_task_branch(self):
        """Test the update method of SymErgCoder for adding a model task branch.
        Asserts that the new model branch is created in the repository.
        """
        model_branch = f"model_{self.branch[4]}"
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", model_branch],
            check=True
        )
        self.ergon[4].update({"topic": model_branch, "payload": self.ergon[4]})
        branches = subprocess.run(
            ["git", "-C", self.repo.local, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn(model_branch, branches.stdout)

    def test_update_delete_model_task_branch(self):
        """Test the update method of SymErgCoder for deleting a model task branch.
        Asserts that the specified model branch is removed from the repository.
        """
        model_branch = f"model_{self.branch[5]}"
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", model_branch],
            check=True
        )
        self.ergon[5].branches.append(model_branch)
        self.ergon[5].update({"topic": model_branch, "payload": self.ergon[5]})
        branches = subprocess.run(
            ["git", "-C", self.repo.local, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertNotIn(model_branch, branches.stdout)

    def test_update_code(self):
        """Test the update method of SymErgCoder for updating code.
        Asserts that the updated code is included in the commit history of the relevant branch.
        """
        model = os.path.basename(self.symerg_coder.name_or_path)
        topic_branch = f"{model}_{self.branch[6]}"
        self.assertEqual(topic_branch, "model_TestCase_uvwx")
        self.symerg_coder.attach_ergon(self.ergon[6])
        self.ergon[6].prompt = f"destination: {self.destination_file}, source: {self.source_file}"

        self.ergon[6].prompt.append("test update code")
        message = {
            "topic": topic_branch,
            "payload": self.ergon[6].prompt,
            "comment": self.ergon[6].prompt[-1]
        }

        with patch.object(AutoTokenizer, "from_pretrained") as pretrained_tokenizer, \
                patch.object(AutoModelForCausalLM, "from_pretrained") as pretrained_model:
            pretrained_tokenizer.return_value = self.tokenizer
            pretrained_model.return_value = self.model

            self.symerg_coder.update(message)
            revision_range = f"{self.branch[6]}..{topic_branch}"
            output = subprocess.run(
                ["git", "-C", self.repo.local, "log", "--oneline", revision_range],
                capture_output=True,
                text=True,
                check=True
            )
        self.assertIn(self.ergon[6].prompt[-1], output.stdout)
