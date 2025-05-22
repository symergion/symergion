import os
import shutil
import subprocess
import unittest

from utils.setup_test import get_test_config
from utils.setup_test import create_test_ergon
from ergon.code import ErgonCode
from git.repository import Repo


class TestCreateTestErgon(unittest.TestCase):
    """This class contains unit tests for the `create_test_ergon` function.
    It sets up a mock Git repository with a default branch and a source file,
    then tests the creation of a new branch and an ErgonCode object.
    """

    def setUp(self):
        """Sets up the test environment by creating a mock Git repository.
        Initializes the repository with:
            - default branch,
            - user configuration,
            - sample source file.
        """
        remote_repo = "/test_repo"
        os.mkdir(remote_repo)
        self.default_branch = "main"
        subprocess.run(
            ["git", "-C", remote_repo, "init", "-b", self.default_branch, remote_repo],
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
        self.repo = Repo(remote_repo, self.default_branch)

    def tearDown(self):
        """Cleans up the test environment by removing the mock Git repositories.
        """
        shutil.rmtree(self.repo.remote)
        shutil.rmtree(self.repo.local)

    def test_get_test_config(self):
        """Test the retrieval of the test configuration.
        This method verifies that the `get_test_config` function correctly
        loads and returns the test configuration from the specified path.
        """
        handler_config, test_case_template = get_test_config()
        self.assertEqual(handler_config, {
            "cache_size": 1,
            "response_cache_size": 100,
            "ntokens": 128,
            "default_branch": "main",
            "task_branch_spec": "task_branch:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)",
            "checkpoints": [{
                "name_or_path": "/test/model",
                "trait": "coding"
            }],
            "templates": {
                "TestCase": {
                    "params": {
                        "source": "source:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)[\\n]?",
                        "destination": "destination:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)(?:[\\s]?|[\\n]?)"
                    },
                    "call_to_action": "Create unittest TestCase",
                    "code_starter": "import unittest\n"
                }
            }
        })
        self.assertEqual(test_case_template, {
            "params": {
                "source": "source:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)[\\n]?",
                "destination": "destination:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)(?:[\\s]?|[\\n]?)"
            },
            "call_to_action": "Create unittest TestCase",
            "code_starter": "import unittest\n"
        })

    def test_create_test_ergon(self):
        """Test the `create_test_ergon` function to ensure it correctly
        creates a new branch and an ErgonCode object with the expected attributes:
        - creates a new branch named 'test_branch',
        - verifies that the returned branch name matches 'test_branch',
        - checks that the returned ergon object is an instance of ErgonCode,
        - asserts that the task type of the ErgonCode object is 'TestCode',
        - ensures that the ErgonCode object's parameters contain the correct keys,
        - validates that the call_to_action in the ErgonCode template is correct,
        - confirms that the code_starter in the ErgonCode template is correct,
        - checks that the ErgonCode object's associated repository matches the test repository.
        """
        test_branch = "test_branch"
        branch, ergon = create_test_ergon(self.repo, test_branch)

        self.assertEqual(branch, test_branch)
        self.assertIsInstance(ergon, ErgonCode)
        self.assertEqual(ergon.task_type, "TestCode")
        self.assertSetEqual(set(ergon.params.keys()), {"source", "destination"})
        self.assertEqual(ergon.template["call_to_action"], "Create unittest TestCase")
        self.assertEqual(ergon.template["code_starter"], "import unittest\n")
        self.assertEqual(ergon.repo, self.repo)
