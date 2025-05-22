from collections import Counter
from collections.abc import Iterable


class CustomList(list):
    """A custom list class that extends Python's built-in list with additional functionality.
    """

    def __contains__(self, other):
        """Check if the CustomList contains another iterable or a single element.

        If `other` is a string or bytes, or not an iterable, it checks for direct containment.
        Otherwise, it checks if all elements of `other`
        are present in the CustomList in the same order.

        Parameters:
            other: The element or iterable to check for containment.

        Returns:
            bool: True if `other` is contained within the CustomList, False otherwise.
        """
        if isinstance(other, (str, bytes)) or not isinstance(other, Iterable):
            return super().__contains__(other)

        for item in other:
            if item not in self:
                return False

        start_index = self.index(other[0])
        return self[start_index: start_index + len(other)] == other

    def __sub__(self, other):
        """Subtract another list from the CustomList.

        This method returns a new CustomList
        containing elements that are in the original CustomList
        but not in the `other` list.
        The subtraction respects the count of each element.

        Args:
            other: The list to subtract from the CustomList.

        Returns:
            CustomList: A new CustomList with elements subtracted.

        Raises:
            ValueError: if `other` is not a list.
        """
        if not isinstance(other, list):
            raise ValueError(f"Subtructed element is not a list {other}")

        self_counter = Counter(self)
        other_counter = Counter(other)
        result_counter = self_counter - other_counter

        result_list = []
        reverse = self.copy()
        reverse.reverse()

        for e in reverse:
            if result_counter[e] > 0:
                result_list.append(e)
                result_counter[e] -= 1

        result_list.reverse()
        return CustomList(result_list)
