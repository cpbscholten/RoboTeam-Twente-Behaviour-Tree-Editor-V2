from pathlib import Path

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot

from model.tree import NodeTypes, Tree, Collection


class MainWorker(QObject):
    """
    Thread that handles the main interaction with the model
    Uses signalling to communicate results with the ui thread
    """

    # signals
    # signal when opening a collection is finished:
    # return a Dictionary of categories with a lost of filenames
    open_collection_finished_signal = pyqtSignal(Collection)
    # signal when opening tree from collection is finished
    # returns category filename and the tree object
    open_tree_from_collection_finished_signal = pyqtSignal(str, str, Tree)
    # signal when writing collection is finished
    # return if writing succeeded or not TODO add details if there were errors?
    write_collection_finished_signal = pyqtSignal(bool)
    # write tree finished
    # return tree and if writing succeeded or not TODO add details if there were errors?
    write_tree_finished_signal = pyqtSignal(str, str, Tree, bool)
    write_tree_custom_path_finished_signal = pyqtSignal(Path, Tree, bool)
    # signal when opening node_types is finished
    # returns the node types dictionary with list of lists for each type
    open_node_types_finished_signal = pyqtSignal(NodeTypes)

    def __init__(self):
        super().__init__()
        # crete collection variable and initialize from settings
        self.collection = Collection.from_path()
        # create node types variable and initialize from settings
        self.node_types = NodeTypes.from_csv()

    @pyqtSlot()
    @pyqtSlot(Path)
    def open_collection(self, path: Path=None):
        """
        PyqtSlot for opening a a collection
        Sends a open_collection_finished_signal when finished
            with a dictionary of categories containing a list of filenames
        :param path: the path to open from, None if the user
                        wants to open from the default settings path
        """
        # todo error handling when reading
        self.collection = Collection.from_path(path)
        self.open_collection_finished_signal.emit(self.collection)

    @pyqtSlot(Collection)
    @pyqtSlot(Collection, Path)
    def write_collection(self, collection: Collection, path: Path=None):
        """
        pyqtSlot for writing a collection
        Emits a write_collection_finished signal
            with a boolean if writing succeeded or not
        :param collection: the collection to write
        :param path: the path to write to, None if writing to path in collection or Settings
        """
        try:
            self.collection = collection
            self.collection.write_collection(path)
            self.write_collection_finished_signal.emit(True)
        # todo catch more specific exceptions
        except:
            self.write_collection_finished_signal.emit(False)

    @pyqtSlot(str, str, Tree)
    def write_tree(self, category: str, filename: str, tree: Tree):
        """
        Writes a tree to the current collection
        Emits a write_tree_finished_signal with a boolean
            if writing succeeded or not
        :param category: the category of the tree
        :param filename: the filename of the tree
        :param tree: the Tree to write
        """
        # todo error handling
        # todo add to collection if tree does not exist yet
        # todo fix merge issues with write_tree method later
        try:
            self.collection.write_tree(tree, self.collection.jsons_path() / category / filename)
            self.write_tree_finished_signal.emit(category, filename, tree, True)
        except:
            # todo catch more specific exceptions
            self.write_tree_finished_signal.emit(category, filename, tree, False)

    @pyqtSlot(Path, Tree)
    def write_tree_custom_path(self, path: Path, tree: Tree):
        """
        Writes a tree to a custom path
        Emits a write_tree_finished_signal with a boolean
            if writing succeeded or not
        :param path: the path to write the tree to
        :param tree: the Tree to write
        """
        # todo error handling
        try:
            self.collection.write_tree(tree, path)
            self.write_tree_custom_path_finished_signal.emit(path, tree, True)
        except:
            # todo catch more specific exceptions
            self.write_tree_custom_path_finished_signal.emit(path, tree, False)

    @pyqtSlot()
    def open_node_types(self):
        """
        Reloads the node types and returns it to the listener as NodeTypes object
        """
        self.node_types = NodeTypes.from_csv()
        self.open_node_types_finished_signal.emit(self.node_types)
