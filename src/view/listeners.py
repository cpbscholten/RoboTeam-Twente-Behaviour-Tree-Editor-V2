from pathlib import Path
from typing import Dict, List

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from controller.workers import MainWorker
from model.tree import Tree, Collection, NodeTypes

import view.windows


class MainListener(QObject):
    """
    Listener that communicates with a controller thread for interaction with the model
    """

    # signals for reading a collection
    # one with a path specified
    # the other without and will use the default path
    open_collection_signal = pyqtSignal()
    open_collection_custom_path_signal = pyqtSignal(Path)

    # signals for writing a collection
    # one with path the other without
    # without path will write to the path in Settings or collection
    write_collection_signal = pyqtSignal(Collection)
    write_collection_custom_path_signal = pyqtSignal(Collection, Path)

    # opens a tree from collection
    # param: category and filename
    open_tree_from_collection_signal = pyqtSignal(str, str)

    # writes a tree
    # one with category and filename to write to the current collection
    # the other path a custom path to write to
    write_tree_signal = pyqtSignal(str, str, Tree)
    write_tree_custom_path_signal = pyqtSignal(Path, Tree)

    # reads the node types json files
    open_node_types_signal = pyqtSignal()

    def __init__(self, gui):
        super().__init__()
        self.gui: view.windows.MainWindow = gui

        # create worker thread and pass it the worker
        self.thread = QThread()
        self.worker = MainWorker()
        self.worker.moveToThread(self.thread)
        self.thread.start()

        # signals and slots for reading a collection
        self.open_collection_signal.connect(self.worker.open_collection)
        self.open_collection_custom_path_signal.connect(self.worker.open_collection)
        self.worker.open_collection_finished_signal.connect(self.open_collection_finished)

        # signals for writing the collection
        self.write_collection_signal.connect(self.worker.write_collection)
        self.write_collection_custom_path_signal.connect(self.worker.write_collection)
        self.worker.write_collection_finished_signal.connect(self.write_collection_finished)

        # signals for writing a tree
        self.write_tree_signal.connect(self.worker.write_tree)
        self.write_tree_custom_path_signal.connect(self.worker.write_tree_custom_path)
        self.worker.write_tree_finished_signal.connect(self.write_tree_finished)
        self.worker.write_tree_custom_path_finished_signal.connect(self.write_tree_custom_path_finished)

        # signals for reading node types
        self.open_node_types_signal.connect(self.worker.open_node_types)
        self.worker.open_node_types_finished_signal.connect(self.open_node_types_finished)

    @pyqtSlot(Collection)
    def open_collection_finished(self, collection: Collection):
        """
        Method that handles the result from controller
        when opening a collection is finished
        Redraws the menu bar
        :param collection: the collection object
        """
        # todo error handling
        self.gui.load_collection = collection
        self.gui.menubar.build_menu_bar(collection)

    @pyqtSlot(list)
    def write_collection_finished(self, errors: List[str]):
        """
        Method that handles the result of writing a collection from the controller
        if it succeeded, update the collection again
        if it failed show an error message
        :param errors: a list with errors
        """
        # update the collection
        if len(errors) == 0:
            view.windows.Dialogs.message_box("Success", 'Tree written successfully!')
            self.open_collection_signal.emit()
        else:
            # show errors
            view.windows.Dialogs.error_box("ERROR", 'There were errors while writing the collection!')

    @pyqtSlot(str, str, Tree, list)
    def write_tree_finished(self, category: str, filename: str, tree: Tree, errors: List[str]):
        """
        Method that handles the result of writing a tree from the controller
        if it succeeded, update the collection again
        if it failed show an error message
        :param category: the category writing to
        :param filename: the filename writing
        :param tree: tree we were trying to write
        :param errors: a list with errors
        """
        # update the collection
        if len(errors) == 0:
            view.windows.Dialogs.message_box("Success", 'Tree written successfully!')
            self.open_collection_signal.emit()
        else:
            # show the failed tree on the screen
            self.gui.show_tree(category, filename, tree)
            view.windows.Dialogs.error_box("ERROR", 'There were errors while writing the tree', errors)

    @pyqtSlot(Path, Tree, list)
    def write_tree_custom_path_finished(self, path: Path, tree: Tree, errors: List[str]):
        """
        Method that handles the result of writing a tree from the controller
        if it succeeded, update the collection again
        if it failed show an error message
        :param path: the path written to
        :param tree: the tree we were trying to write
        :param errors: a list with errors
        """
        # update the collection
        if len(errors) == 0:
            view.windows.Dialogs.message_box("Success", 'Tree {} written successfully!'.format(tree.name))
            self.open_collection_signal.emit()
        else:
            view.windows.Dialogs.error_box("ERROR", 'There were errors while writing tree {} to '.format(tree.name)
                                           + str(path) + '!', errors)

    @pyqtSlot(NodeTypes)
    def open_node_types_finished(self, node_types: NodeTypes):
        """
        Method that handles the result of opening node types
        initializes the node types in the view
        :param node_types: the returned dictionary
        """
        self.gui.load_node_types = node_types
        self.gui.node_types_widget.set_up_node_types(node_types)
