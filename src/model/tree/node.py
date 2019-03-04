import random
import string

from model.config.settings import Settings
from model.exceptions.invalid_tree_json_format_exception import InvalidTreeJsonFormatException
from typing import Dict, List, Any, Union

import logging


class Node:
    logger = logging.getLogger("node")

    def __init__(self, node_id: str, title: str, attributes: Dict[str, Any] = None, children: List[str] = None):
        """
        Constructor for a Node object
        :param node_id: a unique identification string
        :param title: The name of the node
        :param attributes: other attributes with values the nodes has in a dict
        :param children: The id's of the node as children
        """
        self.id: str = node_id
        self.title: str = title
        # if statements and list/dict copies because because of mutability
        self.attributes: Dict[str, Any] = dict(attributes) if attributes is not None else {}
        self.children: List[str] = list(children) if children is not None else []

    @classmethod
    def from_json(cls, node: Dict[str, Any]):
        """
        Alternative constructor to create a node object from a JSON file
        :param node: a node in JSON representation
        :return: a node object with
        :raises InvalidTreeException: If the node misses required attributes or the
                    required attributes have the incorrect type
        """
        attributes = node.copy()
        attributes.pop('children', None)
        if not ('id' in attributes and type(attributes.get('id')) == str
                and 'title' in attributes and type(attributes.get('title')) == str) \
                or ('children' in attributes and not type(attributes.get('children')) == list):
            # TODO: check if children are string?
            Node.logger.error("Attempted to process invalid tree.")
            raise InvalidTreeJsonFormatException
        attributes.pop('id')
        attributes.pop('title')
        return cls(node.get('id'), node.get('title'), attributes, node.get('children'))

    @staticmethod
    def generate_id(size: int = None, chars=string.ascii_lowercase + string.digits) -> str:
        """
        Generates an ID for a node
        :param size: the size of the id, default from settings
        :param chars: type of id, default lowercase and digits
        :return: the generated id
        """
        # set size default value when not initialized
        if size is None:
            size = Settings.query_setting("default_id_size", "Controller")
        return ''.join(random.choice(chars) for _ in range(size))

    def add_child(self, node_id: str):
        """
        Adds a child to a node
        :param node_id: the id of the child
        """
        self.children.append(node_id)

    def remove_child(self, node_id: str):
        """
        Removes a child from the node
        :param node_id: the id of the child
        """
        if node_id not in self.children:
            Node.logger.warning("Attempted to remove non-existent child {} from node {}".format(node_id, self.id))
            return
        self.children.remove(node_id)

    def add_attribute(self, key: str, value: Any):
        """
        Adds an attribute with a value to the node
        :param key: The key of the attribute
        :param value: the value of the attribute
        """
        self.attributes[key] = value

    def remove_attribute(self, key: str):
        """
        Removes an attribute from a node
        :param key: the key of the attribute to remove
        """
        if key not in self.attributes.keys():
            Node.logger.warning("Attempted to remove non-existent attribute {} from node {}".format(key, self.id))
            return
        self.attributes.pop(key)

    def add_property(self, key: str, value: Any):
        """
        Adds a property to a node
        Properties are stored in the attributes section of the node
        :param key: The key of the property
        :param value: the value of the property
        """
        if "properties" not in self.attributes.keys():
            self.attributes["properties"] = {}
        self.attributes["properties"][key] = value

    def remove_property(self, key: str):
        """
        Removes an property from a node
        properties are stored in the attributes section of the node
        :param key: the key of the attribute to remove
        """
        if "properties" not in self.attributes or key not in self.attributes.get("properties"):
            Node.logger.warning("Attempted to remove non-existent attribute {} from node {}".format(key, self.id))
            return
        self.attributes.get("properties").pop(key)

    def properties(self) -> Union[Dict[str, Any], None]:
        """
        Returns the properties dictionary in attributes if it exists
        :return: properties if it exists, else None
        """
        if "properties" in self.attributes:
            return self.attributes.get("properties")
        return None

    def create_json(self) -> Dict[str, Any]:
        """
        Returns a json representation of this node
        :return: A JSON object of this node
        """
        node = self.attributes.copy()
        node['id'] = self.id
        node['title'] = self.title
        if len(self.children) > 0:
            node['children'] = self.children
        return node

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)
