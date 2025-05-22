import os.path


def verified_file_name(repo, file_name, is_new=False):
    """Verifies the validity of a file name within a given repository directory.

    Args:
        repo (str): the root directory of the repository.
        file_name (str): the name of the file to be verified.
        is_new (bool): a flag indicating whether the file is expected to be new or existing.

    Returns:
        str: the verified file name if all checks pass.

    Raises:
        ValueError:
            - if the directory does not exist,
            - if the provided path is a directory,
            - if the file does not exist when it is expected to.
    """
    # Construct the full directory path
    directory = os.path.join(repo, os.path.dirname(file_name))

    # Check if the directory exists
    if not os.path.isdir(os.path.dirname(directory)):
        raise ValueError(f"No such directory `{os.path.dirname(directory)}`")

    # Construct the full file path
    file_path = os.path.join(repo, file_name)

    # Check if the file path is a directory
    if os.path.isdir(file_path):
        raise ValueError(f"`{file_name}` is a directory, provide file name")

    # Check if the file exists when it is expected to
    if not is_new and not os.path.isfile(file_path):
        raise ValueError(f"There is no `{file_name}` file found, provide correct file name")

    # Return the verified file name
    return file_name
