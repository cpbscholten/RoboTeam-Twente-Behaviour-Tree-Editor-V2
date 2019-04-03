import logging
import os
import random
import string
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union

from controller.utils import read_json, write_json, read_csv, write_csv
from model.config import Settings
from model.exceptions import *


class Node:
    logger = logging.getLogger("node")

    def __init__(self, title: str, node_id: str = None, attributes: Dict[str, Any] = None, children: List[str] = None):
        """
        Constructor for a Node object
        :param node_id: a unique identification string
        :param title: The title of the node
        :param attributes: other attributes with values the nodes has in a dict
        :param children: The id's of the node as children
        """
        self.title: str = title
        # generate ID if not provided
        self.id: str = node_id if node_id is not None else Node.generate_id()
        # if statements and list/dict copies because because of mutability
        # A node will always have a title but not always a name, if it has a name it will be saved in attributes
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
            # TODO: provide more elaborate error logging (why is it invalid?)
            Node.logger.error("Attempted to process invalid tree.")
            raise InvalidTreeJsonFormatException
        attributes.pop('id')
        attributes.pop('title')
        return cls(node.get('title'), node.get('id'), attributes, node.get('children'))

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
        :returns True if success, False if node could not be found
        """
        if node_id not in self.children:
            Node.logger.warning("Attempted to remove non-existent child {} from node {}".format(node_id, self.id))
            return False
        self.children.remove(node_id)
        return True

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
        :returns True if success, False if node could not be found
        """
        if key not in self.attributes.keys():
            Node.logger.warning("Attempted to remove non-existent attribute {} from node {}".format(key, self.id))
            return False
        self.attributes.pop(key)
        return True

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
        """
        Equality operator that compares all attributes
        :param other: object to compare against
        :return: if they are equal
        """
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __str__(self):
        """
        string representation of the node
        """
        return str(self.create_json())


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
                "The \"()\" attribute in tree {} is of type {} instead of the "
                "required type {}".format(attribute_name, tree_name, actual_type, required_type))
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
            Tree.logger.error("The \"name\" attribute in tree is missing")
            raise InvalidTreeJsonFormatException
        if not (type(file.get('name')) == str):
            Tree.logger.error(
                "The \"name\" attribute in tree is of type {} instead of "
                "the required type str".format(type(file.get('name'))))
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
            Tree.logger.error("The \"trees[0]\" attribute in tree {} is of type {} instead "
                              "of the required type ()".format(tree_name, type(trees[0]), list))
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
                "The size of the \"nodes\" array in tree {} is of length 0 while its length "
                "should be at least 1".format(tree_name))
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
        # remove root node if trying to remove root
        if self.root == node.id:
            self.root = ''
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
        # remove root node if trying to remove root
        if self.root == node_id:
            self.root = ''
        self.nodes.pop(node_id)
        return True

    def remove_node_and_children_by_id(self, node_id: str) -> bool:
        """
        Removes a node and all of its children recursively
        :param node_id: the id of the node to remvoe
        :return success: if the node and the children were removed successfully
        """
        if node_id not in self.nodes.keys():
            Tree.logger.warning("Attempted to remove non-existent node {} from tree {}".format(node_id, self.name))
            return False
        # remove root node if trying to remove root
        if self.root == node_id:
            self.root = ''
        children = self.nodes.get(node_id).children
        success = True
        if len(children) >= 0:
            for child_id in children:
                success &= self.remove_node_and_children_by_id(child_id)
        self.nodes.pop(node_id, None)
        return success

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

    def __str__(self) -> str:
        """
        String represenatation of the tree
        """
        return str(self.create_json())

    def __eq__(self, other):
        """
        Equality operator for tree, compares all attributes
        """
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)


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
                            logging.info("File at {} is a hidden file, this file will be "
                                         "skipped.".format(os.path.join(sub_root, file)))
                            continue
                        # only parse json files
                        elif file.endswith('.json'):
                            try:
                                json_file: Dict[str, Any] = read_json(Path(sub_root) / file)
                                tree: Tree = Tree.from_json(json_file)
                                # Verify if the tree is valid
                                if not verify:
                                    collection[directory][file] = tree
                                    continue
                                elif len(self.verify_tree(tree)) == 0:
                                    collection[directory][file] = tree
                                else:
                                    # say that tree x in folder y wasn't added
                                    logging.warning("Unable to verify tree {} in {}, this tree will not be added to the"
                                                    " collection".format(tree.name, os.path.join(sub_root, file)))
                            # skip incorrect json files
                            except InvalidTreeJsonFormatException:
                                logging.error("The tree at {} is not a valid tree, this tree will "
                                              "not be loaded".format(os.path.join(sub_root, file)))
                                continue
                        else:
                            # If the file is not a .json log it
                            logging.info("File at {} is not a .json file, this file will be "
                                         "skipped.".format(os.path.join(sub_root, file)))
                    break
            break
        self.collection = collection

    def write_collection(self, path: Path=None) -> List[str]:
        """
        Writes the collection in memory to the given directory
        :param path: the location to write to
        :returns errors, a list with errors that occurred during verification
        """
        errors = []
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
                errors.extend(self.write_tree(content, write_path / filename))
        return errors

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

    def verify_tree(self, tree, category=None, only_check_mathematical_properties=False) -> List[str]:
        """
        Helper method to call the verify tree from verification
        :param tree: the tree to verify
        :param category: the category of the tree
        :param only_check_mathematical_properties: if only the mathematical properties should be checked.
        :return: a list with errors, empty list when no errors occur
        """
        return Verification.verify_tree(self, tree, category, only_check_mathematical_properties)

    def get_root_nodes_by_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Gets all the root nodes from a specific category (Like 'strategies')
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

    def write_tree(self, tree: Tree, path: Path, verify=False) -> List[str]:
        """
        Method that writes a tree to a file
        :param tree: the tree to write
        :param path: the path to write to
        :param verify: verify mathematical properties (False) or full verification (True)
        :return: a list with errors during writing of verification
        """
        errors = self.verify_tree(tree, only_check_mathematical_properties=verify)
        if len(errors) == 0:
            try:
                write_json(path, Tree.create_json(tree))
            except Exception:
                error = 'An exception occurred when writing tree {}.'.format(tree.name)
                Tree.logger.error(error)
                errors.extend(error)
        else:
            error = 'Tree {} could not be written as there were errors during verification'.format(tree.name)
            Tree.logger.error(error)
            errors.append(error)
        return errors

    def categories_and_filenames(self) -> Dict[str, List[str]]:
        """
        Helper method that create a dictionary of categories and filenames
        :return: a dictionary containing categories with a list of tuples with filenames
        """
        result = {}
        for category, items in self.collection.items():
            result[category] = sorted(list(items.keys()))
        return result

    def jsons_path(self):
        """
        Helper method to find the correct path to save to
        :return: the path to save to
        """
        if self.path is None:
            return Settings.default_json_folder()
        else:
            return self.path

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)


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
        return Node(node_type[0], attributes=attributes)

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

    def __str__(self):
        """
        String representation of the node types class
        """
        return str(self.node_types)


class Verification:
    logger = logging.getLogger('verification')

    # todo fix coverage for verification
    @staticmethod
    def verify_tree(collection: Collection, tree: Tree, category=None,
                    only_check_mathematical_properties=False) -> List[str]:
        """
        Function to verify if a tree is valid according to the definition of a tree. So being acyclic and having no
        unconnected nodes in short. But also according to the definition of a behaviour tree and
        lastly if the structure is correct (Strategy -> Tactic -> Role with compositors and decorators in between) if
        a category is given.
        :param collection: the collection the tree is in, to verify against
        :param tree: The tree to verify
        :param category: The category node (Role, Strategy or Tactic for example), used to verify the structure of the
        tree. The default argument is None, if category is None then we don't check the structure of the tree as defined
        by RoboTeam. This is to retain the functionality of verifying the properties, but with the exception of skipping
        some properties.
        :param only_check_mathematical_properties: Boolean value if we only want to check the mathematical properties
        of the tree
        :return: A list with errors, it the list is empty, no errors were found
        """
        # first check mathematical properties and return them if any errors were found
        errors = Verification.verify_mathematical_properties(tree)
        if len(errors) is not 0:
            return errors

        if not only_check_mathematical_properties:
            errors.extend(Verification.verify_non_mathematical_properties(collection, category, tree))
        return errors

    @staticmethod
    def verify_mathematical_properties(tree: Tree):
        """
        Helper method to call helper methods for verifying mathematical properties of the tree
        (If there are no cycles, and if there are no unconnected nodes)
        :param tree: the tree to verify
        :return: a list with errors, empty list if valid
        """
        errors = []

        # check validity of root
        errors.extend(Verification.check_root_validity(tree))
        if len(errors) is not 0:
            return errors

        # Check for cycles
        visited_nodes = {}
        errors.extend(Verification.contains_cycles(tree, visited_nodes))
        if len(errors) is not 0:
            return errors

        # Check for unconnected nodes (and if there's only one root)
        errors.extend(Verification.has_unconnected_nodes(visited_nodes, tree.nodes, tree))
        return errors

    @staticmethod
    def verify_non_mathematical_properties(collection: Collection, category: str, tree: Tree) -> List[str]:
        """
        Helper method that calls the helper methods to check the non-mathematical properties of the verification
        :param collection: the collection of the tree
        :param category: the category of the tree
        :param tree: the tree to verify
        :return: a list with errors, empty if no errors
        """
        errors = []
        errors.extend(Verification.check_category_structure(collection, category, tree))
        errors.extend(Verification.check_composites_and_decorators(tree, tree.root))
        errors.extend(Verification.check_role_inheritance(tree, tree.root))
        return errors

    @staticmethod
    def check_root_validity(tree: Tree) -> List[str]:
        """
        Helper method that checks if the root of the tree exists and if the root actually is an existent node
        :param tree: the tree to check the root of
        :return: a list with errors, empty list if valid
        """
        errors = []
        root = tree.root
        # check existence of root and validity of root node
        if not root or root == '':
            error = 'The tree {} does not have a root and cannot be validated'.format(tree.name)
            errors.append(error)
        elif root not in tree.nodes.keys():
            error = 'The root node with id {} in tree {} does not exist.'.format(root, tree.name)
            errors.append(error)
        return errors

    @staticmethod
    def has_unconnected_nodes(visited_nodes, tree_nodes, tree) -> List[str]:
        """
        Helper function to compare two lists of nodes to see if all the visited nodes are within a list of tree nodes,
        if there are unconnected nodes then go through the list to log which ones are unconnected.
        :param visited_nodes: List of visited nodes.
        :param tree_nodes: List of nodes in the tree.
        :param tree: the tree object verifying
        :return: True if there are no unconnected nodes
        """
        errors = []
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
                    error = "The node {} is unconnected in tree {}".format(visited_node, tree.title)
                    Verification.logger.error(error)
                    errors.append(error)
        return errors

    @staticmethod
    def contains_cycles(tree: Tree, visited_nodes) -> List[str]:
        """
        Helper function to check if a tree contains cycles, given a tree and list of visited nodes.
        :param tree: The tree to check
        :param visited_nodes: The nodes visited
        :return: a list with errors, empty if there are no cycles
        """
        to_visit = [tree.root]
        while True:
            # node_to_visit is the id represented as a string
            node_to_visit = to_visit.pop()
            if node_to_visit in visited_nodes:
                error = "Cycle found in tree {} at node {} while verifying.".format(tree.name, node_to_visit)
                Verification.logger.error(error)
                return list(error)
            visited_nodes[node_to_visit] = tree.nodes[node_to_visit]
            for node in tree.nodes[node_to_visit].children:
                to_visit.append(node)
            if len(to_visit) == 0:
                break
        return []

    @staticmethod
    def check_role_inheritance(tree, current_node: str, current_role=None) -> List[str]:
        """
        Method to check that the ROLE properties are properly inherited to the children
        :param tree: the tree of which to check the ROLE inheritance
        :param current_node: the node currently checking. (first run = root)
        :param current_role: the role that should be inherited
        :return: a list with errors
        """
        errors = []
        children = tree.nodes[current_node].children
        current_node_properties = tree.nodes[current_node].properties()
        if current_node_properties is None:
            if current_role is not None:
                error = "Error in structure of tree {}, node {} has no properties, but should inherit the " \
                        "{} ROLE property from parent".format(tree.name, current_node, current_role)
                Verification.logger.error(error)
                errors.append(error)
        elif "ROLE" in current_node_properties.keys():
            if current_role is None:
                current_role = current_node_properties["ROLE"]
            else:
                if not current_role == current_node_properties["ROLE"]:
                    error = "Error in structure of tree {}, node {} has ROLE property {}, but should inherit" \
                            "{} from parent".format(tree.name, current_node,
                                                    current_node_properties["ROLE"], current_role)
                    Verification.logger.error(error)
                    errors.append(error)

        # Walk the children of the current node
        for child in children:
            errors.extend(Verification.check_role_inheritance(tree, child, current_role))

        return errors

    @staticmethod
    def check_category_structure(collection: Collection, category: str, tree: Tree):
        """
        Helper function to check if the tree has a Strategy -> Tactic -> Role structure, which is defined as a structure
        by the RoboTeam.
        :param collection: the collection the tree is in
        :param category: the category of the tree
        :param tree: The tree to check the structure of
        :return: a list with errors, empty list if no errors
        """
        errors = []
        root = tree.root

        # Is a category given? If so, check the tree structure
        if category is not None:
            # First check if the root node is of the required type
            category_root_nodes = collection.get_root_nodes_by_category(category)
            found = False
            for category_root_node in category_root_nodes:
                if category_root_node[0] == root:
                    found = True
                    break
            if not found:
                error = "Error in structure of tree {}, root node was supposed to be a {} but was a {}" \
                    .format(tree.name, category, collection.get_category_from_node(root))
                Verification.logger.error(error)
                errors.append(error)
                return errors

            # Walk the tree different ways depending on the category
            passed_nodes = [False]*3
            if category == "strategies":
                passed_nodes = [False, False, False]
            elif category == "tactics":
                passed_nodes = [True, False, False]
            elif category == "roles":
                passed_nodes = [True, True, False]

            # Check validity by walking the tree and verifying properties defined by behaviour trees and RoboTeam
            errors.extend(Verification.check_category_structure_recursive_step(collection, tree, root, passed_nodes))
        return errors

    @staticmethod
    def check_category_structure_recursive_step(collection: Collection, tree: Tree, current_node: str,
                                                passed_nodes: [bool], first_step: bool=True) -> List[str]:
        """
        Helper function for the recursive step
        to check if the tree has a Strategy -> Tactic -> Role structure, which is defined as a structure
        by the RoboTeam.
        :param collection: the collection the tree is in
        :param tree: The tree to check the structure of
        :param current_node: The node currently checking
        :param passed_nodes: the nodes already checked
        :param first_step: first time running recursive step
        :return: a list with errors, empty list if no errors
        """
        node_types = NodeTypes.from_csv()
        current_node_types = node_types.get_node_type_by_name(tree.nodes[current_node].title)
        children = tree.nodes[current_node].children
        current_node_type_is_sequence = False

        errors = []

        for current_node_type in current_node_types:
            current_type = current_node_type[0]
            # Composites only have one entry in their list, so we're allowed to do this
            current_type_name = current_node_type[1][0]
            if current_type == "composites":
                if "Sequence" in current_type_name:
                    current_node_type_is_sequence = True

        # If we're at a leaf node (and not the root node) check if all node types have been passed
        if len(children) == 0 and not first_step:
            if "name" not in tree.nodes[current_node].attributes:
                valid_walk = passed_nodes == [True] * 3
                if valid_walk is False:
                    error = "Error in structure of tree {}, the path to leaf node {} does not follow the " \
                            "Strategy -> Tactic -> Role pattern".format(tree.name, current_node)
                    Verification.logger.error(error)
                    errors.append(error)
                return errors
            else:
                current_node_name = tree.nodes[current_node].attributes["name"]
                # If the name of the leaf does not match the current tree (to prevent cycles)
                if tree.name != tree.nodes[current_node].title:
                    tree = collection.get_tree_by_name(current_node_name)
                    current_node = tree.root
        current_node_category = collection.get_category_from_node(current_node)
        if current_node_category == "strategies":
            # We check if it's still false, because we can't pass the same node type twice.
            if passed_nodes[0] is False:
                passed_nodes[0] = True
            else:
                error = "Error in structure of tree {}, the path to node {} encountered " \
                        "strategies twice".format(tree.name, current_node)
                Verification.logger.error(error)
                errors.append(error)
                raise errors
        elif current_node_category == "tactics":
            # We check if it's still false, because we can't pass the same node type twice.
            if passed_nodes[1] is False:
                passed_nodes[1] = True
            else:
                error = "Error in structure of tree {}, the path to node {} " \
                        "encountered tactics twice".format(tree.name, current_node)
                Verification.logger.error(error)
                errors.append(error)
                raise errors
        elif current_node_category == "roles" or tree.nodes[current_node].title == "Role":
            # We check if it's still false, because we can't pass the same node type twice.
            if passed_nodes[2] is False:
                passed_nodes[2] = True
            else:
                error = "Error in structure of tree {}, the path to node {} " \
                        "encountered roles twice".format(tree.name, current_node)
                Verification.logger.error(error)
                errors.append(error)
                return errors
        # Check for Keeper property here, since this kind of can replace Role apparently.
        elif tree.nodes[current_node].properties() is not None \
                and "ROLE" in tree.nodes[current_node].properties().keys() \
                and tree.nodes[current_node].properties()["ROLE"] == "Keeper":
            passed_nodes[2] = True

        # Walk the children of the current node
        for child in tree.nodes[current_node].children:
            # If the current node is a sequence, we must only walk nodes that are not conditions
            if current_node_type_is_sequence:
                child_node_type = node_types.get_node_type_by_name(tree.nodes[child].title)
                # TODO: Are we sure the first entry in the list is always a condition?
                if len(child_node_type) > 0 and child_node_type[0][0] == "conditions":
                    # If the child of a sequence is a condition, then we don't walk it
                    continue
            errors.extend(Verification.check_category_structure_recursive_step(collection, tree,
                          child, passed_nodes.copy(), first_step=False))
        return errors

    @staticmethod
    def check_composites_and_decorators(tree: Tree, current_node: str) -> List[str]:
        """
        Checks the number of children composites and decorators can have
        :param tree: the tree to check
        :param current_node: the node to recursively check
        :return: a list with errors, if none an empty list
        """
        node_types = NodeTypes.from_csv()
        current_node_types = node_types.get_node_type_by_name(tree.nodes[current_node].title)
        children = tree.nodes[current_node].children
        current_node_type_is_sequence = False
        errors = []

        for current_node_type in current_node_types:
            current_type = current_node_type[0]
            # Composites only have one entry in their list, so we're allowed to do this
            current_type_name = current_node_type[1][0]
            # Decorators should have only one child
            if current_type == "decorators":
                if len(children) != 1:
                    error = "Error in structure of tree {}, node {} is a decorator which should have 1 child," \
                            " but it has {} children".format(tree.name, current_node, len(children))
                    Verification.logger.error(error)
                    errors.append(error)

            # Composites should have one or more children
            if current_type == "composites":
                if len(children) < 1:
                    error = "Error in structure of tree {}, node {} is a compositor and should have more " \
                            "than 1 child, but it has 0".format(tree.name, current_node)
                    Verification.logger.error(error)
                    errors.append(error)
                if "Sequence" in current_type_name:
                    current_node_type_is_sequence = True

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
                    # Else walk normally recursively
                    errors.extend(Verification.check_composites_and_decorators(tree, child))
            else:
                errors.extend(Verification.check_composites_and_decorators(tree, child))
        return errors
