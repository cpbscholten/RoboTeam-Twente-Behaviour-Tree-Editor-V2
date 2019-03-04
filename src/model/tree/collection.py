from pathlib import Path
from typing import Dict, Any

from model.exceptions.invalid_tree_json_format_exception import InvalidTreeJsonFormatException
from model.tree.tree import Tree
from controller.utils.file_utils import read_json
from model.tree.verification import Verification
from model.config.settings import Settings

import os
import logging


class Collection:
    logger = logging.getLogger("collection")

    def __init__(self, collection: Dict[str, Dict[str, Tree]] = None):
        """
        Initializes a collection with a given dict
        :param collection: the collection of files
        """
        self.collection: Dict[str, Dict[str, Tree]] = dict(collection) if collection is not None else {}

    @classmethod
    def from_path(cls, path: Path=None):
        """
        Constructor creating a collection from a given location
        :param path: the path containing the directories with jsons
        :return: the generated collection object
        """
        collection = cls()
        collection.build_collection(path)
        return collection

    def build_collection(self, path: Path = None):
        """
        Reads all the json files in the first subdirectories and creates Tree objects from them
        :param path: the path of the main JSON folder
        """
        # set the path to the path specified in settings if None
        if path is None:
            path = Settings.default_json_folder()
        # clean the current collection
        collection = {}
        # find the current directories in the main json folder and create dict for each
        # skip branch checking in coverage as the loop will only be executed once
        for root, dirs, _ in os.walk(str(path)):     # pragma: no branch
            for directory in dirs:
                collection[directory] = {}
                # for each directory make a tree object of each json file inside the folder
                # add the object to the dict of that folder
                # skip branch checking in coverage as the loop will only be executed once
                for sub_root, _, files in os.walk(os.path.join(root, directory)):    # pragma: no branch
                    for file in files:
                        # skip hidden files
                        if file[0] == '.':
                            continue
                        # only parse json files
                        elif file.endswith('.json'):
                            try:
                                json_file: Dict[str, Any] = read_json(Path(sub_root) / file)
                                tree: Tree = Tree.from_json(json_file)
                                # Verify if the tree is valid
                                # TODO fix coverage
                                if Verification.verify(tree):
                                    collection[directory][file] = tree
                                else:
                                    pass
                                    # todo fix coverage
                                    # TODO: say that tree x in folder y wasn't added
                            # skip incorrect json files
                            except InvalidTreeJsonFormatException:
                                # TODO better error handling and more information in log
                                continue
                    break
            break
        self.collection = collection

    def write_collection(self, path: Path=None):
        """
        Writes the collection in memory to the given directory
        :param path: the location to write to
        """
        # set the path to the path specified in settings if None
        if path is None:
            path = Settings.default_json_folder()
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
                content.write(write_path, filename)

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
        """
        if not (directory in self.collection.keys() and filename in self.collection[directory].keys()):
            Collection.logger.warning("The requested tree {} to be removed could not be found".format(filename))
            return
        self.collection[directory].pop(filename)

    def remove_tree_by_name(self, directory: str, name: str):
        """
        Removes a tree from the collection from the requested directory by name
        :param directory: the directory of the tree
        :param name: the name of the tree file
        """
        if directory in self.collection.keys():
            for key, value in self.collection[directory].items():
                if value.name == name:
                    self.remove_tree(directory, key)
                    return
        Collection.logger.warning("The requested tree {} to be removed could not be found".format(name))

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)
