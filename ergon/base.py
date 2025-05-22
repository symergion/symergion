from abc import abstractmethod
from observer import Observer


class Ergon(Observer):
    """Base Ergon abstract class:
    Any ergon implementation should derive from this class

    - observe and complete action requests from SymErg

    Attributes:
        _name (str): The name of the Ergon instance.
    """
    def __init__(self, name):
        """Initialize an Ergon instance.

        Args:
            name (str): The name of the Ergon instance.
        """
        self._name = name

    @property
    def name(self):
        """Get the name of the Ergon instance.

        Returns:
            str: the name of the Ergon instance.
        """
        return self._name

    @abstractmethod
    def update(self, message):
        """Abstract method to be implemented by subclasses.

        This method is called when there is an update or action request from SymErg.

        Args:
            message (dict): The message or data related to the update.

        Raises:
            NotImplementedError: if the subclass does not implement this method.
        """
        raise NotImplementedError
