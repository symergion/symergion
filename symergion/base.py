from abc import abstractmethod
from observer import Observer


class SymErgion(Observer):
    """Base SymErgion abstract class:
        Any symergion implementation should derive from this class:
            - observes complete actions
            - attach, detach SymErgs
            - attach, detach Ergons
            - request Ergons to complete actions
    """

    def __init__(self):
        """Initialize the SymErgion with empty SymErgs and Ergons lists.
        """
        self._symergs = []
        self._ergons = []

    @property
    def symergs(self):
        """Get a list of SymErgs.

        Returns:
            list of SymErg: SymErgs
        """
        return self._symergs

    @property
    def ergons(self):
        """Get a list of Ergons.

        Returns:
            list of Ergon: Ergons
        """
        ergons = [ergon for symerg in self.symergs for ergon in symerg.ergons]
        return list(set(ergons))

    def attach_symerg(self, symerg):
        """Attaches a SymErg to the SymErgion.

        Args:
            symerg (SymErg): the SymErg to be attached
        """
        if symerg not in self.symergs:
            self._symergs.append(symerg)

    def detach_symerg(self, symerg):
        """Detaches a SymErg from the SymErgion.

        Args:
            symerg (SymErg): the SymErg to be detached
        """
        if symerg in self.symergs:
            self._symergs.remove(symerg)

    @abstractmethod
    def update(self, message):
        """Updates the SymErgion with a message.

        Args:
            message (dict): the message to update with

        Raises:
            NotImplementedError: if the method is not implemented by a subclass
        """
        raise NotImplementedError

    @abstractmethod
    def instantiate_symerg(self, checkpoint):
        """Instantiates a new SymErg based on a checkpoint.

        Args:
            checkpoint (dict): the checkpoint to use for instantiation

        Raises:
            NotImplementedError: if the method is not implemented by a subclass
        """
        raise NotImplementedError

    @abstractmethod
    def instantiate_ergon(self, name):
        """Instantiates a new Ergon with a given name.

        Args:
            name (str): the name of the Ergon to instantiate

        Raises:
            NotImplementedError: if the method is not implemented by a subclass
        """
        raise NotImplementedError

    @abstractmethod
    def decomission_ergon(self, ergon):
        """Decomissions an Ergon.

        Args:
            ergon (Ergon): the Ergon to decommission

        Raises:
            NotImplementedError: if the method is not implemented by a subclass
        """
        raise NotImplementedError

    @abstractmethod
    def _notify(self, message, symergs):
        """Notifies specified SymErgs with a message.

        Args:
            message (dict): the message to notify with
            symergs (list of SymErgs): the SymErgs to notify

        Raises:
            NotImplementedError: if the method is not implemented by a subclass
        """
        raise NotImplementedError
