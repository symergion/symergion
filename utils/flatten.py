def flatten(nested_list):
    """Flatten two level nested list into a single-level list

    Args:
        nested_list (list of lists): A list where each element is also a list.

    Returns:
        list: A flattened list containing all elements from the nested lists.

    Example:
        >>> flatten([[1, 2], [3, 4]])
        [1, 2, 3, 4]
    """
    flatten_list = []

    for element in nested_list:
        flatten_list.extend(element)

    return flatten_list
