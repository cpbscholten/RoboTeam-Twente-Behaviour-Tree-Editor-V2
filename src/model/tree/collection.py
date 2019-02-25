from typing import Dict, Any

from model.exceptions.TreeNotFoundException import TreeNotFoundException
from model.exceptions.InvalidTreeException import InvalidTreeException
from model.tree.tree import Tree
from controller.utils.json_utils import read_json, write_json

import os

# TODO: Read path from config
DEF_PATH = "/home/christian/PycharmProjects/roboteam_ai-development/roboteam_ai/src/jsons/"


class Collection:
    def __init__(self, collection: Dict[str, Dict[str, Tree]] = None):
        """
        Initializes a collection with a given dict
        :param collection: the collection of files
        """
        self.collection: Dict[str, Dict[str, Tree]] = dict(collection) if collection is not None else {}

    @classmethod
    def from_path(cls, path: str):
        """
        Constructor creating a collection from a given location
        :param path: the path containing the directories with jsons
        :return: the generated collection object
        """
        collection = cls()
        collection.build_collection(path)
        return collection

    def build_collection(self, path: str = DEF_PATH):
        """
        Reads all the json files in the first subdirectories and creates Tree objects from them
        :param path: the path of the main JSON folder
        """
        # clean the current collection
        collection = {}
        # find the current directories in the main json folder and create dict for each
        # skip branch checking in coverage as the loop will only be executed once
        for root, dirs, _ in os.walk(path):     # pragma: no branch
            for directory in dirs:
                collection[directory] = {}
                # for each directory make a tree object of each json file inside the folder
                # add the object to the dict of that folder
                # skip branch checking in coverage as the loop will only be executed once
                for sub_root, _, files in os.walk(root + directory):    # pragma: no branch
                    for file in files:
                        # skip hidden files
                        if file[0] == '.':
                            continue
                        # only parse json files
                        elif file.endswith('.json'):
                            try:
                                json_file: Dict[str, Any] = read_json(os.path.join(sub_root, file))
                                tree: Tree = Tree.from_json(json_file)
                                collection[directory][file] = tree
                            # skip incorrect json files
                            except InvalidTreeException:
                                # TODO better error handling and logging
                                continue
                    break
            break
        self.collection = collection

    def write_collection(self, path: str = DEF_PATH):
        """
        Writes the collection in memory to the given directory
        :param path: the location to write to
        """
        # make a copy of the current collection
        collection = dict(self.collection)
        # read each nested dictionary and write each file in that directory
        for directory, files in collection.items():
            # create directories if it does not exist
            if not os.path.isdir(path + directory):
                os.makedirs(path + directory)
            for name, content in files.items():
                write_json(os.path.join(path + directory, name), Tree.create_json(content))

    def add_tree(self, directory: str, name: str, tree: Tree):
        """
        Adds a tree to a directory in the collection
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
        Removes a tree from the collection from the requested directory
        :param directory: the directory of the tree
        :param filename: the name of the tree file
        :raises TreeNotFoundException if the requested tree does not exist
        """
        if not (directory in self.collection.keys() and filename in self.collection[directory].keys()):
            raise TreeNotFoundException
        self.collection[directory].pop(filename)

    def remove_tree_by_name(self, directory: str, name: str):
        if directory in self.collection.keys():
            for key, value in self.collection[directory].items():
                if value.name == name:
                    self.remove_tree(directory, key)
                    return
        raise TreeNotFoundException

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)
