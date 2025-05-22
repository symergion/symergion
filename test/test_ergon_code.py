import unittest
from unittest.mock import Mock

import os
import shutil
import subprocess

from git.repository import Repo
from ergon.base import Ergon
from ergon.code import ErgonCode
from ergon.prompt import Prompt

from utils import read_text_file
from utils.setup_test import get_test_config


class TestErgonCode(unittest.TestCase):
    """This class contains test cases for the ErgonCode class.
    """

    def setUp(self):
        """Sets up the environment before each test case.
        Initializes a remote repository, creates branches, and sets up an ErgonCode instance.
        """
        remote_repo = "/test_repo"
        os.mkdir(remote_repo)
        default_branch = "main"
        subprocess.run(
            ["git", "-C", remote_repo, "init", "-b", default_branch, remote_repo],
            check=True
        )
        config = f"{remote_repo}/.git/config"
        subprocess.run(
            ["git", "-C", remote_repo, "config", "-f", config, "user.email", "test@localhost"],
            check=True
        )
        subprocess.run(
            ["git", "-C", remote_repo, "config", "-f", config, "user.name", "Test User"],
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

        self.mock_repo = Mock()

        self.branch = {
            1: "TestCase_abcd",
            2: "TestCase_efgh",
            3: "TestCase_ijkl",
            4: "TestCase_mnop",
            5: "TestCase_qrst",
            "wrong_branch": "TestCase_uvwx"
        }
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", self.branch.get(1)],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.repo.local, "push", "--set-upstream", "origin", self.branch.get(1)],
            check=True
        )
        reasoner = Mock()
        reasoner.name_or_path = "test_reasoner"
        reasoner.generate = lambda *args, **kwargs: "reasoning"
        self.reasoners = [reasoner]
        _, test_case_template = get_test_config()
        self.ergon = ErgonCode(
            task_type="TestCode",
            template=test_case_template,
            repo=self.repo,
            feature_branch=self.branch.get(1),
            reasoners=self.reasoners
        )
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", self.branch.get(2)],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.repo.remote, "branch", self.branch.get(4)],
            check=True
        )
        self.destination_file = "test_destination_file"
        self.name_or_path = "/test/model"

    def tearDown(self):
        """Cleans up the environment after each test case.
        Removes the remote and local repositories.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_init(self):
        """Tests the initialization of the ErgonCode instance.
        Checks if the instance:
            - is an instance of Ergon,
            - has the correct name, repository, task type, branches, and default branch.
        Also checks if the ergon branch exists in the local repository.
        """
        self.assertIsInstance(self.ergon, Ergon)
        self.assertEqual(self.ergon.name, self.branch.get(1))
        self.assertEqual(self.ergon.repo.local, self.repo.local)
        self.assertEqual(self.ergon.task_type, "TestCode")
        self.assertIn(self.branch.get(1), self.ergon.branches)
        self.assertIn(self.branch.get(1), self.ergon.branches)
        branches = subprocess.run(
            ["git", "-C", self.ergon.repo.local, "branch"],
            check=True,
            capture_output=True,
            text=True
        )
        self.assertIn(self.ergon.name, branches.stdout)
        self.assertIsInstance(self.ergon.reasoners, list)
        self.assertEqual(self.ergon.reasoners[0].name_or_path, self.reasoners[0].name_or_path)

    def test_prompt(self):
        """Tests the setting and manipulation of the prompt in the ErgonCode instance.
        Checks if:
            - the destination and source files are correctly set,
            - the prompt is an instance of Prompt,
            - the source file content is included in the prefix,
            - additional prompts can be appended.
        """
        self.ergon.prompt = f"destination: {self.destination_file}, source: {self.source_file}"
        source = read_text_file(os.path.join(self.repo.local, self.source_file))

        self.assertEqual(self.ergon.destination_file, self.destination_file)
        self.assertEqual(self.ergon.source_file, self.source_file)
        self.assertIsInstance(self.ergon.prompt, Prompt)
        self.assertIn(source, self.ergon.prompt.prefix)

        self.ergon.prompt.append("another prompt")
        self.assertIn("another prompt", self.ergon.prompt)

    def test_checkout_existing_locally(self):
        """Tests checking out an existing local branch.
        Checks if the branch is checked out correctly
        by verifying the current branch in the local repository.
        """
        self.ergon.checkout(self.branch.get(1))
        git_status = subprocess.run(
            ["git", "-C", self.repo.local, "status", "-sb"],
            check=True,
            capture_output=True,
            text=True
        )

        self.assertIn(self.branch.get(1), git_status.stdout)

    def test_checkout_existing_remotely(self):
        """Tests checking out an existing remote branch.
        - Creates a new branch on the remote,
        - checks it out,
        - verifies if the branch is checked out correctly.
        """
        branch = f"some_model_{self.branch.get(1)}"
        subprocess.run(
            ["git", "-C", self.repo.remote, "branch", branch],
            check=True
        )
        self.ergon.checkout(branch)
        git_status = subprocess.run(
            ["git", "-C", self.repo.local, "status", "-sb"],
            check=True,
            capture_output=True,
            text=True
        )

        self.assertIn(branch, git_status.stdout)

    def test_checkout_not_existing(self):
        """Tests checking out a non-existing branch.
        Checks if the branch is created and checked out correctly
        by verifying the current branch in the local repository.
        """
        self.ergon.checkout(self.branch.get(5))
        git_status = subprocess.run(
            ["git", "-C", self.repo.local, "status", "-sb"],
            check=True,
            capture_output=True,
            text=True
        )

        self.assertIn(self.branch.get(5), git_status.stdout)

    def test_respond(self):
        """Tests the respond method of the ErgonCode instance.
        Checks if:
            the response is written to the destination file,
            the change is committed correctly.
        """
        self.ergon.repo.checkout(self.branch.get(1))
        response = "test_respond"
        self.ergon.prompt = f"destination: {self.destination_file}, source: test_source_file"
        self.ergon.prompt.append(response)
        self.ergon.respond(self.branch.get(1), response, "test_respond")
        with open(os.path.join(self.repo.local, self.destination_file), "r", encoding="utf-8") as f:
            written = f.read()

        self.assertEqual(written, response)
        log = subprocess.run(
            ["git", "-C", self.repo.local, "log", "--oneline", "-1"],
            check=True,
            capture_output=True,
            text=True
        )
        self.assertIn(response, log.stdout)

    def test_update_correct_topic(self):
        """Tests updating the ErgonCode instance with a correct topic.
        Checks if:
            the destination and source files are correctly set,
            the response is appended to the prompt,
            the changes are committed correctly.
        """
        model = os.path.basename(self.name_or_path)
        topic_branch = f"{self.branch.get(1)}_{model}"
        message = {
            "topic": topic_branch,
            "payload": f"destination: {self.destination_file}, source: {self.source_file}",
            "comment": f"destination: {self.destination_file}, source: {self.source_file}"
        }
        self.ergon.prompt = message.get("payload")
        self.ergon.update(message)

        self.assertEqual(self.ergon.destination_file, self.destination_file)
        self.assertEqual(self.ergon.source_file, self.source_file)

        message = {
            "topic": topic_branch,
            "payload": "test",
            "comment": "test"
        }
        self.ergon.prompt.append(message.get("payload"))
        self.ergon.update(message)
        revision_range = f"{self.branch.get(1)}..{topic_branch}"
        output = subprocess.run(
            ["git", "-C", self.repo.local, "log", "--oneline", revision_range],
            check=True,
            capture_output=True,
            text=True
        )

        self.assertIn("test", output.stdout)

    def test_update_wrong_topic(self):
        """Tests updating the ErgonCode instance with a wrong topic.
        Checks if the response is not committed to the wrong branch.
        """
        model = os.path.basename(self.name_or_path)
        topic_branch = f"{model}_{self.branch.get('wrong_branch')}"
        message = {
            "topic": topic_branch,
            "payload": "test"
        }
        self.ergon.destination_file = self.destination_file
        self.ergon.update(message)
        commits = f"{self.branch.get('wrong_branch')}..{topic_branch}"
        output = subprocess.run(
            ["git", "-C", self.repo.local, "log", "--oneline", commits, "--"],
            check=False,
            capture_output=True,
            text=True
        )

        self.assertNotIn(f"Response for {self.branch.get('wrong_branch')}\n", output.stdout)

    def test_update_delete_model_branch(self):
        """Tests updating the ErgonCode instance with a delete operation on a model branch.
        Checks if the model branch is deleted correctly.
        """
        model_branch = f"model_{self.branch.get(3)}"
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", self.branch.get(3)],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", model_branch],
            check=True
        )
        ergon3 = ErgonCode(
            task_type="TestCode",
            template={
                "source_code": True,
                "call_to_action": "Create unittest TestCase for ",
                "code_starter": "import unittest\n"
            },
            repo=self.repo,
            feature_branch=self.branch.get(3)
        )
        ergon3.branches.append(model_branch)
        ergon3.update({"topic": model_branch, "payload": ergon3})
        branches = subprocess.run(
            ["git", "-C", self.ergon.repo.local, "branch"],
            check=True,
            capture_output=True,
            text=True
        )

        self.assertNotIn(model_branch, branches.stdout)

    def test_update_add_model_branch(self):
        """Tests updating the ErgonCode instance with an add operation on a model branch.
        Checks if the model branch is added correctly.
        """
        topic_branch = f"model_{self.branch.get(1)}"
        subprocess.run(
            ["git", "-C", self.repo.local, "branch", topic_branch],
            check=True
        )
        message = {
            "topic": topic_branch,
            "payload": self.ergon
        }
        self.ergon.update(message)

        self.assertEqual(topic_branch, self.ergon.branches[-1])

    def test_initial_message(self):
        """Tests response on consistent and inconsistent messages
        """
        ergon = ErgonCode("task_type", "template", self.mock_repo, "feature_branch")
        ergon.branches.append("test_symerg_feature_branch")

        self.mock_repo.get_objects_messages = lambda b: [
            "message1",
            "message2"
        ]
        self.mock_repo.get_ergon_branch_messages = lambda b: [
            "message1",
            "message2"
        ]
        self.assertEqual(ergon.initial_message, "message2")

        self.mock_repo.get_objects_messages = lambda b: [
            "message",
            b
        ]
        self.mock_repo.get_ergon_branch_messages = lambda b: [
            "message",
            b
        ]
        with self.assertRaises(ValueError):
            ergon.initial_message
