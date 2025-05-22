from abc import ABC, abstractmethod


class Observer(ABC):
    """Base Observer abstract class.
        Any observer implementation should derive from this class
        and implement the `update` method to handle notifications from the subject.
    """

    @abstractmethod
    def update(self, message):
        """Update method that needs to be implemented by concrete observers.

        Args:
            message (str): The message or data sent from the subject.

        Raises:
            NotImplementedError: if the derived class does not implement this method.
        """
        raise NotImplementedError
