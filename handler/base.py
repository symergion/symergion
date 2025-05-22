from abc import ABC, abstractmethod


class Handler(ABC):
    """Base Handler abstract class:

        Any handler implementation should derive from this class.
        Any subclass must implement the `dispatch` and `sync_state` methods.
    """

    def __init__(self, symergion):
        """Initialize the Handler with a Symergion instance.
            symergion (SymErgion): an instance of the Symergion class or a similar object.
        """
        self.symergion = symergion
        print(f"Handler is being instantiated for SymErgion {self.symergion}")

    @abstractmethod
    def dispatch(self, event):
        """Dispatch an event to be handled.
        This method must be implemented by any subclass.
        It should handle the given event appropriately.

        Args:
            event: The event to be dispatched.

        Raises:
            NotImplementedError: if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def sync_state(self):
        """Synchronize the internal state with the external system.
        This method must be implemented by any subclass.
        It should ensure that the internal state is in sync with the external system.

        Raises:
            NotImplementedError: if the method is not implemented by a subclass.
        """
        raise NotImplementedError
