from model.exceptions.InvalidTreeException import InvalidTreeException
from model.exceptions.ChildNotFoundException import ChildNotFoundException
from model.exceptions.AttributeNotFoundException import AttributeNotFoundException
from typing import Dict, List, Any

import logging

logger = logging.getLogger("node")


class Node:
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
            # TODO more elaborate error logging
            logger.error("Attempted to process invalid tree.")
            raise InvalidTreeException
        attributes.pop('id')
        attributes.pop('title')
        return cls(node.get('id'), node.get('title'), attributes, node.get('children'))

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
        :raises ChildNotFoundException: when the node does not have this child
        """
        if node_id not in self.children:
            # TODO more elaborate error logging
            logger.error("Attempted to remove non-existent child () from node ()".format(node_id, self.id))
            raise ChildNotFoundException
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
        :raises AttributeNotFoundException: when the attribute does not exist
        """
        if key not in self.attributes.keys():
            # TODO more elaborate error logging
            logging.error("Attempted to remove non-existent attribute () from node ()".format(key, self.id))
            raise AttributeNotFoundException
        self.attributes.pop(key)

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
