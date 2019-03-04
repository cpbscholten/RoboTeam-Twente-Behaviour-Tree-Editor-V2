import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

from controller.utils.file_utils import write_csv, read_csv
from model.config.settings import Settings
from model.exceptions.invalid_node_type_exception import InvalidNodeTypeException
from model.tree.node import Node


class NodeTypes:
    logger = logging.getLogger("node_types")

    def __init__(self, node_types: Dict[str, List[List[str]]]=None, path: Path=None):
        """
        initializes node types
        :param node_types: dictionary with categories containing node types list.
                            first entry o list contains the name of the node type
        :param path: path of the test nodes files
        """
        self.path: Path = path
        # set to dict() if empty, due to mutability issues in python
        self.node_types: Dict[str, List[List[str]]] = node_types if not None else dict()

    @classmethod
    def from_csv(cls, path: Path=None):
        """
        Creates an object with default node types from csv config files
        :param path: the path of the csv files, defaults to config/node_types/
        :raises InvalidNodeTypesConfigFileException: when an invalid file is given
        :return: an object containing the default node objects with the required attributes and maximum
                number of children allowed
        """
        # set default path, for when Settings.NODE_TYPES_PATH changes
        if path is None:
            read_path = Settings.default_node_types_folder()
        else:
            read_path = path
        node_types = {}
        read_path = read_path / ''
        # pragma no branch for coverage, because the for loop will only be executed once
        for root, _, files in os.walk(str(read_path)):     # pragma: no branch
            # iterate over all csv files
            for file in files:
                # skip hidden files
                if file[0] == '.':
                    continue
                # only parse csv files
                elif file.endswith('.csv'):
                    # create a category from the filename by removing .csv
                    filename_without_csv = file[:-4]
                    csv_file: List[List[str]] = read_csv(Path(root) / file)
                    node_types[filename_without_csv] = csv_file
            break
        # only write path if the given variable is not None
        return cls(node_types, path)

    def write(self, path: Path=None):
        """
        Writes the default node types back to the config file
        :param path: the path to write to defaults to config/node_types/
        """
        # change path if specified
        if path is None and self.path is None:
            path = Settings.default_node_types_folder()
        elif path is None and self.path is not None:
            path = self.path
        # writes each category to a csv file in the path
        for category, csv_content in self.node_types.items():
            write_csv(path / (category + '.csv'), csv_content)

    @staticmethod
    def check_node_type_validity(node_type: List[str]) -> bool:
        """
        checks if the node_type is valid
        :param node_type: a list containing a node type. First value is the name
        :raises InvalidNodeTypeException: if a node_type is invalid
        """
        if len(node_type) == 0 or not all(isinstance(n, str) for n in node_type):
            NodeTypes.logger.error("The node type {} is not valid and cannot be used.".format(node_type))
            raise InvalidNodeTypeException
        return True

    @staticmethod
    def create_node_from_node_type(node_type: List[str]) -> Node:
        """
        Static method to create a node object from a node with a provided node_type dictionary
        :param node_type: the dictionary containing the attributes the node requires and the name is first entry
        :return: a node created from the node type dictionary
        """
        # check if the new node_type is valid
        NodeTypes.check_node_type_validity(node_type)
        # the attributes from the node type will be added as a dict in the attributes
        properties = {}
        attributes = {"properties": properties}
        # iterate over the node type, except the name
        for attribute in node_type[1:]:
            properties[attribute] = ""
        return Node(Node.generate_id(), node_type[0], attributes)

    def add_node_type(self, category: str, name: str, attributes: List[str]=None):
        """
        adds a new node type and stores it to the config file.
        :param category: the category of the node_type
        :param name: the name of the node type
        :param attributes: optional list of the required attributes
        """
        # create new category if it does not exist
        if category not in self.node_types.keys():
            self.node_types[category] = []
        node_type = [name]
        # extend the node type list with attributes if they exist
        if attributes is not None:
            node_type.extend(attributes)
        # adds the node type to the requested category
        self.node_types.get(category).append(node_type)

    def remove_node_type(self, category: str, node_type: List[str]):
        """
        Removes the requested node type object from the requested category
        Asks for the category and node_type object to be sure that the correct object gets removed
        :param category: the category of the node_type
        :param node_type: a list containing the node_type
        """
        if category in self.node_types.keys() and node_type in self.node_types.get(category):
            self.node_types.get(category).remove(node_type)
        NodeTypes.logger.warning("The requested node type {} in category {} "
                                 "could not be found and removed".format(node_type, category))

    def update_node_type(self, category: str, old: List[str], updated: List[str]):
        """
        Updates the old node type in the category to the new node type
        :param category: the category the node type is in
        :param old: the node_type to be updated
        :param updated: the node_type that replaces the old entry
        """
        # check if the new node_type is valid
        NodeTypes.check_node_type_validity(updated)
        # replace the old node_type with the new node_type if the old exists
        if category in self.node_types.keys() and old in self.node_types.get(category):
            index = self.node_types.get(category).index(old)
            self.node_types.get(category)[index] = updated

    def add_category(self, category: str):
        """
        Adds a category to the node types file and saves
        :param category: the name of the category to add
        """
        if category not in self.node_types.keys():
            self.node_types[category] = []

    def remove_category(self, category: str):
        """
        Removes a category with the node_types from the config file
        :param category: the name of the category
        """
        if category not in self.node_types.keys():
            NodeTypes.logger.warning("Category {} does not exist and cannot be removed "
                                     "from node types".format(category))
        self.node_types.pop(category, None)

    def get_node_type_by_name(self, name: str) -> List[Tuple[str, List[str]]]:
        """
        Returns the node_types with the requested name.
        :param name: the name to look for in node_types
        :return: list of tuples with the category and node_type list
        """
        result = []
        for category, node_types in self.node_types.items():
            for node_type in node_types:
                if node_type[0] == name:
                    result.append((category, node_type))
        return result

    def get_node_type_by_node(self, node: Node) -> List[Tuple[str, List[str]]]:
        """
        Helper function for finding all node types corresponding to a node object
        :param node: the node to find a node_type for
        :return: list of tuples with the category and node_type list
        """
        return self.get_node_type_by_name(node.title)

    def __eq__(self, other):
        """
        Override default equality operator to not compare
        the path but only the node_types list for testing purposes
        :param other: the object to compare against
        """
        return (isinstance(other, self.__class__)
                and self.node_types == other.node_types)
