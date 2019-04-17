from pathlib import Path

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot

from model.tree import NodeTypes, Tree, Collection

from controller.tree_data import *


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
    # return a list of errors
    write_collection_finished_signal = pyqtSignal(list)
    # write tree finished
    # return tree and a list with possible errors
    write_tree_finished_signal = pyqtSignal(str, str, Tree, list)
    write_tree_custom_path_finished_signal = pyqtSignal(Path, Tree, list)
    # signal when opening node_types is finished
    # returns the node types dictionary with list of lists for each type
    open_node_types_finished_signal = pyqtSignal(NodeTypes)
    # signal when DB query is finished
    # sends a dictionary with node ids as keys and heatmap values as vals to the view
    db_query_finished_signal = pyqtSignal(dict, str)

    def __init__(self):
        super().__init__()
        # crete collection variable and initialize from settings
        self.collection = Collection.from_path()
        # create node types variable and initialize from settings
        self.node_types = NodeTypes.from_csv()

    # noinspection PyArgumentList
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
        self.collection = Collection.from_path(path)
        self.open_collection_finished_signal.emit(self.collection)

    # noinspection PyArgumentList
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
        self.collection = collection
        errors = self.collection.write_collection(path)
        self.write_collection_finished_signal.emit(errors)

    # noinspection PyArgumentList
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
        errors = self.collection.write_tree(tree, self.collection.jsons_path() / category / filename)
        self.write_tree_finished_signal.emit(category, filename, tree, errors)

    # noinspection PyArgumentList
    @pyqtSlot(Path, Tree)
    def write_tree_custom_path(self, path: Path, tree: Tree):
        """
        Writes a tree to a custom path
        Emits a write_tree_finished_signal with a boolean
            if writing succeeded or not
        :param path: the path to write the tree to
        :param tree: the Tree to write
        """
        errors = self.collection.write_tree(tree, path)
        self.write_tree_custom_path_finished_signal.emit(path, tree, errors)

    # noinspection PyArgumentList
    @pyqtSlot()
    def open_node_types(self):
        """
        Reloads the node types and returns it to the listener as NodeTypes object
        """
        self.node_types = NodeTypes.from_csv()
        self.open_node_types_finished_signal.emit(self.node_types)

    # noinspection PyArgumentList
    @pyqtSlot(str, str)
    def create_heatmap(self, tid: str, status_type: str):
        """
        Fetches data necessary for heatmap, calculates heatmap values, and tells view to display it.
        """
        node_dict = {}

        # Setup DB connection
        session = Setup.get_session()
        query = session.query(TreeNode).filter_by(tree_id=tid)

        # Determine which status we're interested in
        if not query.count():
            return
        for node in query:
            if status_type == "Success":
                node_dict[node.id] = node.successes
            elif status_type == "Running":
                node_dict[node.id] = node.runnings
            elif status_type == "Waiting":
                node_dict[node.id] = node.waitings
            else:
                node_dict[node.id] = node.failures
        total_count = sum(node_dict.values())
        average = total_count / len(node_dict)
        heatmap_dict = {}

        # Calculate the percentage (node's status count divided by total status count) for each node
        for key in node_dict.keys():
            heatmap_dict[key] = node_dict[key] / average
        max_value = max(map(abs, node_dict.values()))
        adjustment = 2.0 / max_value
        for key, value in node_dict.items():
            heatmap_dict[key] = value * adjustment
        self.db_query_finished_signal.emit(heatmap_dict, status_type)
