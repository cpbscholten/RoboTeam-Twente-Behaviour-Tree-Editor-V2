from pathlib import Path
from typing import Dict, Any, Tuple, List

from model.config.node_types import NodeTypes
from model.exceptions.cycle_in_tree_exception import CycleInTreeException
from model.exceptions.incorrect_tree_structure_exception import IncorrectTreeStructureException
from model.exceptions.invalid_tree_json_format_exception import InvalidTreeJsonFormatException
from model.exceptions.unconnected_node_exception import UnconnectedNodeException
from model.tree.tree import Tree
from controller.utils.file_utils import read_json
from model.config.settings import Settings
from controller.utils.file_utils import write_json

import os
import logging


class Collection:
    logger = logging.getLogger("collection")

    def __init__(self, collection: Dict[str, Dict[str, Tree]]=None, path: Path=None):
        """
        Initializes a collection with a given dict
        :param collection: the collection of files
        :param path: the path of the collection None if using custom path
        """
        self.path = path
        self.collection: Dict[str, Dict[str, Tree]] = dict(collection) if collection is not None else {}

    @classmethod
    def from_path(cls, path: Path=None, verify: bool=True):
        """
        Constructor creating a collection from a given location
        :param path: the path containing the directories with jsons
        :param verify: boolean to tell if we should verify the tree while building the collection
        :return: the generated collection object
        """
        collection = cls(None, path)
        collection.build_collection(path, verify)
        return collection

    def build_collection(self, path: Path=None, verify: bool=True):
        """
        Reads all the json files in the first subdirectories and creates Tree objects from them
        :param verify: boolean to tell if we should verify the tree while building the collection
        :param path: the path of the main JSON folder
        """
        # set the path to the path specified in settings if None
        if path is None:
            path = Settings.default_json_folder()
        # clean the current collection
        collection = {}
        # create default categories in collection
        for category in Settings.default_collection_categories():
            collection[category] = {}
        # find the current directories in the main json folder and create dict for each
        # skip branch checking in coverage as the loop will only be executed once
        for root, dirs, _ in os.walk(str(path)):     # pragma: no branch
            for directory in dirs:
                # skip hidden directories
                if directory[0] == '_' or directory[0] == ".":
                    continue
                collection[directory] = {}
                # for each directory make a tree object of each json file inside the folder
                # add the object to the dict of that folder
                # skip branch checking in coverage as the loop will only be executed once
                for sub_root, _, files in os.walk(os.path.join(root, directory)):    # pragma: no branch
                    for file in files:
                        # skip hidden files
                        if file[0] == '.':
                            logging.info("File at {} is a hidden file, this file will be skipped.".format(os.path.join(sub_root, file)))
                            continue
                        # only parse json files
                        elif file.endswith('.json'):
                            try:
                                json_file: Dict[str, Any] = read_json(Path(sub_root) / file)
                                tree: Tree = Tree.from_json(json_file)
                                # Verify if the tree is valid
                                # TODO fix coverage
                                if not verify:
                                    collection[directory][file] = tree
                                    continue
                                elif self.verify_tree(tree):
                                    collection[directory][file] = tree
                                else:
                                    # todo fix coverage
                                    # say that tree x in folder y wasn't added
                                    logging.warning("Unable to verify tree {} in {}, this tree will not be added to the collection".format(tree.name, os.path.join(sub_root, file)))
                            # skip incorrect json files
                            except InvalidTreeJsonFormatException:
                                logging.error("The tree at {} is not a valid tree, this tree will not be loaded".format(os.path.join(sub_root, file)))
                                continue
                        else:
                            # If the file is not a .json log it
                            logging.info("File at {} is not a .json file, this file will be skipped.".format(os.path.join(sub_root, file)))
                    break
            break
        self.collection = collection

    def write_collection(self, path: Path=None):
        """
        Writes the collection in memory to the given directory
        :param path: the location to write to
        """
        # set the path to the path specified in settings if None
        if path is None and self.path is None:
            path = Settings.default_json_folder()
        elif path is None and self.path is not None:
            path = self.path
        # make a copy of the current collection
        collection = dict(self.collection)
        # read each nested dictionary and write each file in that directory
        for directory, files in collection.items():
            # create directories if it does not exist
            write_path = path / directory
            if not os.path.isdir(write_path):
                os.makedirs(str(write_path))
            for filename, content in files.items():
                # write collection
                self.write_tree(content, write_path / filename)

    def add_tree(self, directory: str, name: str, tree: Tree):
        """
        Adds a tree to a directory in the collection
        overrides a tree if it already exists, so can also be used for updating
        :param directory: the directory the tree needs to be in
        :param name: the name of the file
        :param tree: the tree object
        """
        if directory in self.collection.keys():
            self.collection[directory][name] = tree
        else:
            self.collection[directory] = {name: tree}

    def remove_tree(self, directory: str, filename: str):
        """
        Removes a tree from the collection from the requested directory by filename
        :param directory: the directory of the tree
        :param filename: the name of the tree file
        :returns True if success, False if tree was not found
        """
        if not (directory in self.collection.keys() and filename in self.collection[directory].keys()):
            Collection.logger.warning("The requested tree {} to be removed could not be found".format(filename))
            return False
        self.collection[directory].pop(filename)
        return True

    def remove_tree_by_name(self, directory: str, name: str):
        """
        Removes a tree from the collection from the requested directory by name
        :param directory: the directory of the tree
        :param name: the name of the tree file
        :returns True if success, False if tree was not found
        """
        if directory in self.collection.keys():
            for key, value in self.collection[directory].items():
                if value.name == name:
                    self.remove_tree(directory, key)
                    return True
        Collection.logger.warning("The requested tree {} to be removed could not be found".format(name))
        return False

    def get_tree_by_name(self, name: str) -> Tree:
        for directory in self.collection.keys():
            for key, value in self.collection[directory].items():
                if value.name == name:
                    return value

    # TODO: Check if root node is actually in the tree (also do this in verification)
    # TODO: Return a list of problems instead of just False
    # TODO: Check if only leaf nodes can only be subtrees
    def verify_tree(self, tree, category=None) -> bool:
        """
        Function to verify if a tree is valid according to the definition of a tree. So being acyclic and having no
        unconnected nodes in short. But also according to the definition of a behaviour tree and lastly if the structure is
        correct (Strategy -> Tactic -> Role with compositors and decorators in between)
        :param tree: The tree to verify
        :param category: The category node (Role, Strategy or Tactic for example), used to verify the structure of the
        tree. The default argument is None, if category is None then we don't check the structure of the tree as defined
        by RoboTeam. This is to retain the functionality of verifying the properties, but with the exception of skipping
        some properties.
        :return: True if the tree is verified
        """
        # Check for cycles
        visited_nodes = {}
        root = tree.root

        # Is a category given? If so, check the tree structure
        if category is not None:
            # First check if the root node is of the required type
            category_root_nodes = self.get_root_nodes_by_category(category)
            found = False
            for category_root_node in category_root_nodes:
                if category_root_node[0] == root:
                    found = True
                    break
            if not found:
                self.logger.error("Error in structure of tree {}, root node was supposed to be a {} but was a {}"
                                  .format(tree.name, category, self.get_category_from_node(tree.root)))
                return False

            # Walk the tree different ways depending on the category
            passed_nodes = [False]*3
            if category == "strategies":
                passed_nodes = [False, False, False]
            elif category == "tactics":
                passed_nodes = [True, False, False]
            elif category == "roles":
                passed_nodes = [True, True, False]

            # Check validity by walking the tree and verifying properties defined by behaviour trees and RoboTeam
            valid = self.walk_tree(tree, tree.root, passed_nodes, first_step=True)

            if not valid:
                self.logger.error("Error in structure of tree {}, one or more of the paths to the leaf nodes does not follow Strategy -> Tactic -> Role"
                                  .format(tree.name))
                return False

        # Check for cycles
        try:
            self.contains_cycles(tree, visited_nodes)
        except CycleInTreeException:
            return False

        # Check for unconnected nodes (and if there's only one root)
        try:
            self.has_unconnected_nodes(visited_nodes, tree.nodes, tree)
        except UnconnectedNodeException:
            return False

        # If the above checks don't raise an exception the tree is valid.
        return True

    def contains_cycles(self, tree: Tree, visited_nodes):
        """
        Helper function to check if a tree contains cycles, given a tree and list of visited nodes.
        :param tree: The tree to check
        :param visited_nodes: The nodes visited
        :return: True if there are no cycles in the tree.
        :raises CycleInTreeException, if there is a cycle in the tree
        """
        to_visit = [tree.root]
        while True:
            # node_to_visit is the id represented as a string
            node_to_visit = to_visit.pop()
            if node_to_visit in visited_nodes:
                self.logger.error("Cycle found in tree {} at node {} while verifying.".format(tree.name, node_to_visit))
                raise CycleInTreeException
            visited_nodes[node_to_visit] = tree.nodes[node_to_visit]
            for node in tree.nodes[node_to_visit].children:
                to_visit.append(node)
            if len(to_visit) == 0:
                break

    def has_unconnected_nodes(self, visited_nodes, tree_nodes, tree):
        """
        Helper function to compare two lists of nodes to see if all the visited nodes are within a list of tree nodes,
        if there are unconnected nodes then go through the list to log which ones are unconnected.
        :param visited_nodes: List of visited nodes.
        :param tree_nodes: List of nodes in the tree.
        :return: True if there are no unconnected nodes
        :raises UnconnectedNodeException, if there are unconnected nodes in the tree, meaning it is an invalid tree
        """
        if len(visited_nodes) < len(tree_nodes):
            # If there is an unconnected node find it so we can log detailed info
            for visited_node in visited_nodes:
                present = False
                for tree_node in tree_nodes:
                    if tree_node == visited_node:
                        # If the node has been visited break from this loop
                        present = True
                        break
                if present:
                    # The node was present continue checking
                    continue
                else:
                    self.logger.error("The node {} is unconnected in tree {}".format(visited_node, tree.title))
            raise UnconnectedNodeException
        return True

    def walk_tree(self, tree: Tree, current_node: str, passed_nodes: [bool], first_step: bool=False) -> bool:
        """
        Helper function to walk through a tree, verifying its structure (Strategy -> Tactic -> Role)
        :param tree: The tree to walk.
        :param current_node: The current node we're checking.
        :param passed_nodes: An array of passed nodes, the positions of the array are strategy, tactics and role
        respectively. If the tree has them all on True that means all node types were passed while walking to the
        current position.
        :param first_step: Used to indicate if this is the first call, this allows trees with no children to be
        validated.
        :return: True if all paths to all leaves encounter all necessary node types.
        """
        node_types = NodeTypes.from_csv()
        current_node_types = node_types.get_node_type_by_name(tree.nodes[current_node].title)
        children = tree.nodes[current_node].children
        current_node_type_is_sequence = False

        for current_node_type in current_node_types:
            # Decorators should have one child
            current_type = current_node_type[0]
            # Composites only have one entry in their list, so we're allowed to do this
            current_type_name = current_node_type[1][0]
            if current_type == "decorators":
                if len(children) != 1:
                    self.logger.error("Error in structure of tree {}, node {} is a decorator which should have 1 child, but it has {} children".format(tree.name, current_node, len(children)))
                    return False

            # Composites should have one or more children
            if current_type == "composites":
                if len(children) < 1:
                    self.logger.error("Error in structure of tree {}, node {} is a compositor and should have more than 1 child, but it has 0".format(tree.name, current_node))
                    return False
                if "Sequence" in current_type_name:
                    current_node_type_is_sequence = True

        # If we're at a leaf node (and not the root node) check if all node types have been passed
        if len(children) == 0 and not first_step:
            if "name" not in tree.nodes[current_node].attributes:
                valid_walk = passed_nodes == [True]*3
                if valid_walk is False:
                    self.logger.error(
                        "Error in structure of tree {}, the path to leaf node {} does not follow the Strategy -> Tactic -> Role pattern"
                            .format(tree.name, current_node))
                    return False
                return True
            else:
                current_node_name = tree.nodes[current_node].attributes["name"]
                # If the name of the leaf does not match the current tree (to prevent cycles)
                if tree.name != tree.nodes[current_node].title:
                    tree = self.get_tree_by_name(current_node_name)
                    current_node = tree.root
        current_node_category = self.get_category_from_node(current_node)
        if current_node_category == "strategies":
            # We check if it's still false, because we can't pass the same node type twice.
            if passed_nodes[0] is False:
                passed_nodes[0] = True
            else:
                self.logger.error("Error in structure of tree {}, the path to node {} encountered strategies twice"
                        .format(tree.name, current_node))
                raise IncorrectTreeStructureException
        elif current_node_category == "tactics":
            # We check if it's still false, because we can't pass the same node type twice.
            if passed_nodes[1] is False:
                passed_nodes[1] = True
            else:
                self.logger.error("Error in structure of tree {}, the path to node {} encountered tactics twice"
                        .format(tree.name, current_node))
                raise IncorrectTreeStructureException
        elif current_node_category == "roles" or tree.nodes[current_node].title == "Role":
            # We check if it's still false, because we can't pass the same node type twice.
            if passed_nodes[2] is False:
                passed_nodes[2] = True
            else:
                self.logger.error("Error in structure of tree {}, the path to node {} encountered roles twice"
                        .format(tree.name, current_node))
                raise IncorrectTreeStructureException
        # Check for Keeper property here, since this kind of can replace Role apparently.
        elif tree.nodes[current_node].properties() is not None and \
                 tree.nodes[current_node].properties()["ROLE"] == "Keeper":
            passed_nodes[2] = True

        # Walk the children of the current node
        for child in tree.nodes[current_node].children:
            # If the current node is a sequence, we must only walk nodes that are not conditions
            if current_node_type_is_sequence:
                child_node_type = node_types.get_node_type_by_name(tree.nodes[child].title)
                # TODO: Are we sure the first entry in the list is always a condition?
                if len(child_node_type) > 0 and child_node_type[0][0] == "conditions":
                    # If the child of a sequence is a condition, then we don't walk it
                    pass
                else:
                    # Else walk normally
                    try:
                        walk_result = self.walk_tree(tree, child, passed_nodes.copy())
                        if walk_result is False:
                            return False
                    except IncorrectTreeStructureException:
                        return False
            else:
                try:
                    walk_result = self.walk_tree(tree, child, passed_nodes.copy())
                    if walk_result is False:
                        return False
                except IncorrectTreeStructureException:
                    return False

        # Return true if all is good
        return True

    def get_root_nodes_by_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Gets all the rood nodes from a specific category (Like 'strategies')
        :param category: the category to get the root nodes from
        :return: A list of all the root nodes in a category, the list is empty if the category does not exist
        """
        if category not in self.collection:
            return []
        result = []
        trees = self.collection[category]
        for tree in trees:
            result.append((self.collection[category][tree].root, self.collection[category][tree].name))
        return result

    def get_category_from_node(self, node: str) -> str:
        """
        Given a node, find the category of the node if its a root node
        :param node: The node to check the category of
        :return: The category node if its found
        """
        for category in self.collection.keys():
            for tree in self.collection[category]:
                if self.collection[category][tree].root == node:
                    return category

    def write_tree(self, tree: Tree, path: Path):
        if self.verify_tree(tree):
            write_json(path, Tree.create_json(tree))
        else:
            Tree.logger.error('Tree {} is invalid and can not be written'.format(tree.name))

    def categories_and_filenames(self) -> Dict[str, List[str]]:
        """
        Helper method that create a dictionary of categories and filenames
        :return: a dictionary containing categories with a list if filenames
        """
        result = {}
        for category, items in self.collection.items():
            result[category] = sorted(list(items.keys()))
        return result

    def jsons_path(self):
        if self.path is None:
            return Settings.default_json_folder()
        else:
            return self.path

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)
