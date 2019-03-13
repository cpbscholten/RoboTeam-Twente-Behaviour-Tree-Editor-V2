from pathlib import Path

from controller.utils.file_utils import write_json
from model.exceptions.invalid_tree_json_format_exception import InvalidTreeJsonFormatException
from model.tree.node import Node
from typing import Dict, List, Any

import os
import logging


class Tree:
    logger = logging.getLogger("tree")

    def __init__(self, name: str, root: str, nodes: Dict[str, Node] = None):
        """
        Constructor of the Tree object
        :param name: the name of the tree, is the same as the title in the JSON representation
        :param root: The root node of the tree
        :param nodes: a dictionary containing the id of the node as key as the node object as value
        """
        self.name: str = name
        self.root: str = root
        # if statement and dict copy because of mutability
        # TODO: Check if it's valid?
        self.nodes: Dict[str, Node] = dict(nodes) if nodes is not None else {}

    @staticmethod
    def check_presence(tree_name: str, attribute_name: str, dictionary: Dict[str, Any]):
        """
        Static method to check if a key is present in a JSON file and logs the error when it isn't.
        :param tree_name: The name of the tree we're checking this in
        :param attribute_name: The name of the attribute we are checking
        :param dictionary: The dictionary in which the key must be present
        :return: True if the attribute is present
        :raises: InvalidTreeJsonFormatException if the attribute is missing
        """
        if attribute_name not in dictionary:
            Tree.logger.error("The \"{}\" attribute in tree {} is missing".format(attribute_name, tree_name))
            raise InvalidTreeJsonFormatException
        return True

    @staticmethod
    def check_type(tree_name: str, attribute_name: str, dictionary: Dict[str, Any], required_type: type):
        """
        Static method to check if the value in the key-value pair in JSON is of a required type and logs the error when
        it isn't
        :param tree_name: The name of the tree we're checking this in
        :param attribute_name: The name of the attribute we are checking
        :param dictionary: The dictionary in which we are checking the type of the value
        :param required_type: The type which the value is required to be
        :return: True if the attribute is of the correct type
        :raises: InvalidTreeJsonFormatException if the attribute is of the incorrect type
        """
        actual_type = type(dictionary.get(attribute_name))
        if not (actual_type == required_type):
            Tree.logger.error(
                "The \"()\" attribute in tree {} is of type {} instead of the required type {}".format(attribute_name, tree_name, actual_type, required_type))
            raise InvalidTreeJsonFormatException
        return True

    @classmethod
    def from_json(cls, file: Dict[str, Any]):
        """
        Alternative constructor to create a tree  object from a file in json representation
        :param file: a python dictionary containing a tree file
        :return: Tree object containing all attributes from the input
        :raises InvalidTreeException; if required attributes are missing
                    or when required attributes have the wrong type
        """
        # Manually check name first, since we don't know the tree name yet.
        if 'name' not in file:
            Tree.logger.error("The \"name\" attribute in tree is missing")  # TODO: which tree tho?????
            raise InvalidTreeJsonFormatException
        if not (type(file.get('name')) == str):
            Tree.logger.error(
                "The \"name\" attribute in tree is of type {} instead of the required type str".format(type(file.get('name'))))
            raise InvalidTreeJsonFormatException
        tree_name = file.get('name')

        Tree.check_presence(tree_name, 'data', file)
        Tree.check_type(tree_name, 'data', file, dict)

        data = file.get('data')

        Tree.check_presence(tree_name, 'trees', data)
        Tree.check_type(tree_name, 'trees', data, list)

        trees: List[Any] = data.get('trees')
        # Manually check the size of the tree since it must be of size 1.
        trees_size = len(trees)
        if not (trees_size == 1):
            Tree.logger.error(
                "The size of the \"trees\" array in tree {} is of length {} while it should be of length 1".format(
                    tree_name, str(trees_size)))
            raise InvalidTreeJsonFormatException

        # TODO: Add case for tests to make coverage 100%
        # Manually check the type of trees[0] since the helper function does not support that.
        if not (type(trees[0]) == dict):
            Tree.logger.error("The \"trees[0]\" attribute in tree {} is of type {} instead of the required type ()".format(tree_name, type(trees[0]), list))
            raise InvalidTreeJsonFormatException

        tree: Dict[str, Any] = trees[0]

        Tree.check_presence(tree_name, 'root', tree)
        Tree.check_type(tree_name, 'root', tree, str)
        Tree.check_presence(tree_name, 'title', tree)
        Tree.check_type(tree_name, 'title', tree, str)
        Tree.check_presence(tree_name, 'nodes', tree)
        Tree.check_type(tree_name, 'nodes', tree, dict)

        if not (len(tree.get('nodes')) > 0):
            Tree.logger.error(
                "The size of the \"nodes\" array in tree {} is of length 0 while its length should be at least 1".format(
                    tree_name))
            raise InvalidTreeJsonFormatException

        nodes: Dict[str, Any] = {}
        for key, value in tree.get('nodes').items():
            nodes[key] = Node.from_json(value)
        # create the new tree object
        return cls(file.get('name'), tree.get('root'), nodes)

    def add_node(self, node: Node):
        """
        Adds a node to the tree object
        :param node: the node to add to the tree
        """
        self.nodes[node.id] = node

    def remove_node(self, node: Node):
        """
        Removes a node from the tree
        :param node: the node object to remove
        :returns True if success, False if node could not be found
        """
        if node not in self.nodes.values():
            Tree.logger.warning("Attempted to remove non-existent node {} from tree {}".format(node.id, self.name))
            return False
        self.nodes.pop(node.id)
        return True

    def remove_node_by_id(self, node_id: str):
        """
        Removes a node from the tree by id
        :param node_id: The id of the node to remove
        :returns True if success, False if node could not be found
        """
        if node_id not in self.nodes.keys():
            Tree.logger.warning("Attempted to remove non-existent node {} from tree {}".format(node_id, self.name))
            return False
        self.nodes.pop(node_id)
        return True

    def create_json(self) -> Dict[str, Any]:
        """
        Creates a JSON representation of this node
        :return: a JSON representation of this node stored in a dict
        """
        tree: Dict[str, Any] = {'title': self.name, 'root': self.root}
        nodes: Dict[str, Dict[str, Any]] = {}
        for key, value in self.nodes.items():
            nodes[key] = value.create_json()
        tree['nodes'] = nodes
        file = {"name": self.name, "data": {"trees": [tree]}}
        return file

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)
