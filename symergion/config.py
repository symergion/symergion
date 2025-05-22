import json


class Config():
    """A class to handle configuration settings.

    This class can be initialized with a dictionary or loaded from a JSON file.
    It allows accessing configuration settings as attributes.
    """

    @classmethod
    def from_json(cls, json_path):
        """Create a Config instance from a JSON file.

        Args:
            json_path (str): the path to the JSON file containing the configuration.

        Returns:
            Config: an instance of Config initialized with the data from the JSON file.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        obj = cls(json_data)
        return obj

    def __init__(self, json_data=None):
        """Initialize the Config instance.

        Args:
            json_data (dict, optional): the dictionary containing configuration settings.
        """
        if json_data:
            for key, value in json_data.items():
                setattr(self, key, value)

    def __getattr__(self, attr):
        """Get an attribute value.

        If the attribute does not exist, return None instead of raising an AttributeError.

        Args:
            attr (str): the name of the attribute to retrieve.

        Returns:
            Any: a value of the attribute, or None if the attribute does not exist.
        """
        return getattr(self, attr) if attr in self.__dict__ else None
