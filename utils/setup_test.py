from ergon.code import ErgonCode


def get_test_config():
    """Retrieves the configuration settings for creating a test case.

    Returns:
        tuple: A tuple containing the handler configuration dictionary
               and the test case template dictionary.
    """
    test_case_template = {
        "params": {
            "source": "source:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)[\\n]?",
            "destination": "destination:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)(?:[\\s]?|[\\n]?)"
        },
        "call_to_action": "Create unittest TestCase",
        "code_starter": "import unittest\n"
    }
    handler_config = {
        "model_cache_size": 1,
        "response_cache_size": 100,
        "ntokens": 128,
        "default_branch": "main",
        "task_branch_spec": "task_branch:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)",
        "checkpoints": [{
            "name_or_path": "/test/model",
            "trait": "coding"
        }],
        "templates": {
            "TestCase": test_case_template
        }
    }
    return handler_config, test_case_template


def create_test_ergon(repo, branch):
    """Creates a new branch in the given repository
    initializes an ErgonCode object for generating test cases.

    Args:
        repo (object): The repository object where the branch will be created.
        branch (str): The name of the branch to be created.

    Returns:
        tuple: A tuple containing the name of the created branch
        and the initialized ErgonCode object.
    """
    create_branch = ["git", "-C", repo.remote, "branch", branch]
    repo.run_command(create_branch)
    _, test_case_template = get_test_config()
    ergon = ErgonCode(
        task_type="TestCode",
        template=test_case_template,
        repo=repo,
        feature_branch=branch
    )
    return branch, ergon
