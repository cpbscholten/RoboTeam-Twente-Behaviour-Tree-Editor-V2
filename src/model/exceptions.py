class IncorrectTreeStructureException(Exception):
    """
    Is raised when structure of the tree is not correct, for example if the root node is not of the correct type
    """
    pass


class InvalidNodeTypeException(Exception):
    """
    Is raised when the node_types.json file has invalid syntax
    """
    pass


class InvalidTreeJsonFormatException(Exception):
    """
    Exception when a parsed tree is invalid
    """
    pass


class SettingNotFoundException(Exception):
    """
    Exception when a non-existent setting is queried or altered
    """
    pass
