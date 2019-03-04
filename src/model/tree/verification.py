import logging

from model.tree.node import Node
from typing import List

from model.exceptions.cycle_in_tree_exception import CycleInTreeException
from model.exceptions.unconnected_node_exception import UnconnectedNodeException

# TODO fix circular tree import which breaks the code
# due to typing using tree
# from model.tree.tree import Tree


class Verification:
    logger = logging.getLogger("verification")

    @staticmethod
    def verify(tree) -> bool:
        """
        Function to verify if a tree is valid. It does this by looking at the trees properties and by looking at the node
        types that can be defined by the user.
        :param tree: The tree to verify
        :return: True if the tree is valid
        """
        return Verification.verify_tree(tree)  # and verify_nodes(list(tree.nodes.values()))

    @staticmethod
    def verify_tree(tree) -> bool:
        """
        Function to verify if a tree is valid according to the definition of a tree. So being acyclic and having no
        unconnected nodes in short.
        :param tree: The tree to verify
        :return: True if the tree is verified
        :raises: CycleInTreeException, if there is a cycle in the tree, meaning it is an invalid tree.
        :raises: UnconnectedNodeException, if there are unconnected nodes in the tree, meaning it is an invalid tree
        """
        # Check for cycles
        visited_nodes = {}
        root = tree.root

        to_visit = [root]

        while True:
            node_to_visit = to_visit.pop()
            if node_to_visit in visited_nodes:
                # TODO: More elaborate error logging
                raise CycleInTreeException
            visited_nodes[node_to_visit] = tree.nodes[node_to_visit]
            for node in tree.nodes[node_to_visit].children:
                to_visit.append(node)
            if len(to_visit) == 0:
                break

        # Check for unconnected nodes (and if there's only one root)
        if len(visited_nodes) < len(tree.nodes):
            raise UnconnectedNodeException
            # TODO: More elaborate error logging

        # If the above checks don't raise an exception the tree is valid (from a mathematical perspective)
        return True

    # @staticmethod
    # def verify_nodes(nodes: List[Node]) -> bool:
    #     valid = True
    #     for node in nodes:
    #         if not verify_node(node):
    #             valid = False
    #     return valid
    #
    #
    # def verify_node(node: Node) -> bool:
    #     return True
