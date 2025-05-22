import io
from contextlib import redirect_stdout


def capture_output(function, *args, **kwargs):
    """Capture the standard output of a given function when it is executed.
    This function takes another function and its arguments,
    executes the function,
    captures any output that would normally be printed to the console.
    The captured output is then returned as a string.

    Args:
        function (callable): The function whose output needs to be captured.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        str: The captured standard output from the function execution.

    Example:
        >>> def example_function():
        ...     print("Hello, World!")
        >>> output = capture_output(example_function)
        >>> print(output)
        'Hello, World!'
    """
    captured_output = io.StringIO()

    with redirect_stdout(captured_output):
        function(*args, **kwargs)

    output = captured_output.getvalue().strip()
    captured_output.close()

    return output
