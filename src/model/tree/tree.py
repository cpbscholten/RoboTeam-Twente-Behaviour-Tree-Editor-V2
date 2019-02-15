from model.exceptions.InvalidTreeException import InvalidTreeException
from model.exceptions.NodeNotFoundException import NodeNotFoundException
from model.tree.node import Node
from typing import Dict, List, Any


class Tree:
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
        self.nodes: Dict[str, Node] = dict(nodes) if nodes is not None else {}

    @classmethod
    def from_json(cls, file: Dict[str, Any]):
        """
        Alternative constructor to create a tree  object from a file in json representation
        :param file: a python dictionary containing a tree file
        :return: Tree object containing all attributes from the input
        :raises InvalidTreeException; if required attributes are missing
                    or when required attributes have the wrong type
        """
        # TODO cleanup
        if 'name' in file and type(file['name']) == str \
                and 'data' in file and type(file['data']) == dict:
            data = file['data']
            if 'trees' in data and type(data['trees']) == list:
                trees: List[Any] = data['trees']
                if len(trees) == 1 and type(trees[0]) == dict:
                    tree: Dict[str, Any] = trees[0]
                    if 'root' in tree and type(tree['root']) == str \
                            and 'title' in tree and type(tree['title']) == str \
                            and 'nodes' in tree and type(tree['nodes']) == dict \
                            and len(tree['nodes']) > 0:
                        # create node objects for each node and add them to a dict
                        nodes: Dict[str, Any] = {}
                        for key, value in tree.get('nodes').items():
                            nodes[key] = Node.from_json(value)
                        # create the new tree object
                        return cls(file['name'], tree['root'], nodes)
        # TODO more elaborate error logging
        raise InvalidTreeException

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
        :raises NodeNotFoundException: if the tree does not contain this node
        """
        if node not in self.nodes.values():
            # TODO more elaborate error logging
            raise NodeNotFoundException
        self.nodes.pop(node.id)

    def remove_node_by_id(self, id: str):
        """
        Removes a node from the tree by id
        :param id: The id of the node to remove
        :raises NodeNotFoundException: if the tree does not have a node with this id
        """
        if id not in self.nodes.keys():
            # TODO more elaborate error logging
            raise NodeNotFoundException
        self.nodes.pop(id)

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
