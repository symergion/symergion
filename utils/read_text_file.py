import os.path


def read_text_file(file_path):
    """Reads the content of a text file and returns it as a UTF-8 string.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file decoded as UTF-8.

    Raises:
        FileNotFoundError: if the specified file does not exist.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"There is no such file: {file_path}")

    with open(file_path, "rb") as file:
        content = file.read()

    return content.decode(encoding="utf-8", errors="replace")
