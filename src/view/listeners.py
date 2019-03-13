from pathlib import Path
from typing import Dict, List

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from controller.workers import MainWorker
from model.tree import Tree

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
    write_collection_signal = pyqtSignal()
    write_collection_custom_path_signal = pyqtSignal(Path)

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
        self.gui = gui

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

        # signals for retrieving a tree from the collection
        self.open_tree_from_collection_signal.connect(self.worker.open_tree_from_collection)
        self.worker.open_tree_from_collection_finished_signal.connect(
        self.open_tree_from_collection_finished)

        # signals for writing a tree
        self.write_tree_signal.connect(self.worker.write_tree)
        self.write_tree_custom_path_signal.connect(self.worker.write_tree_custom_path)
        self.worker.write_tree_finished_signal.connect(self.write_tree_finished)
        self.worker.write_tree_custom_path_finished_signal.connect(self.write_tree_custom_path_finished)

        # signals for reading node types
        self.open_node_types_signal.connect(self.worker.open_node_types)
        self.worker.open_node_types_finished_signal.connect(self.open_node_types_finished)

    # slots that handle the results of the worker
    @pyqtSlot(dict)
    def open_collection_finished(self, categories_and_filenames: Dict[str, List[str]]):
        """
        Method that handles the result from controller
        when opening a collection is finished
        Redraws the menu bar
        :param categories_and_filenames: dict of categories containing a list of filenames
        """
        # todo error handling
        self.gui.menubar.build_menu_bar(categories_and_filenames)

    @pyqtSlot(str, str, Tree)
    def open_tree_from_collection_finished(self, category: str, filename: str, tree: Tree):
        """
        Method that handles the result of opening a tree from the collection
        Shows it in the main window
        :param category: category of the tree
        :param filename: filename of the tree
        :param tree: tree object from collection
        """
        self.gui.check_unsaved_changes()
        self.gui.load_tree = tree
        self.gui.show_tree(category, filename, tree)

    @pyqtSlot(bool)
    def write_collection_finished(self, success: bool):
        """
        Method that handles the result of writing a collection from the controller
        if it succeeded, update the collection again
        if it failed show an error message
        :param success: if writing succeeded or not
        """
        # update the collection
        if success:
            view.windows.Dialogs.message_box("Success", 'Tree written successfully!')
            self.open_collection_signal.emit()
        else:
            view.windows.Dialogs.error_box("ERROR", 'There were errors while writing the collection, '
                                                    'for more details read the logs!')

    @pyqtSlot(str, str, Tree, bool)
    def write_tree_finished(self, category: str, filename: str, tree: Tree, success: bool):
        """
        Method that handles the result of writing a tree from the controller
        if it succeeded, update the collection again
        if it failed show an error message
        :param category: the category writing to
        :param filename: the filename writing
        :param tree: tree we were trying to write
        :param success: if writing succeeded or not
        """
        # update the collection
        if success:
            view.windows.Dialogs.message_box("Success", 'Tree written successfully!')
            self.open_collection_signal.emit()
        else:
            # show the failed tree on the screen
            self.gui.show_tree(category, filename, tree)
            view.windows.Dialogs.error_box("ERROR", 'There were errors while writing the tree, '
                                                    'for more details read the logs!')

    @pyqtSlot(Path, Tree, bool)
    def write_tree_custom_path_finished(self, path: Path, tree: Tree, success: bool):
        """
        Method that handles the result of writing a tree from the controller
        if it succeeded, update the collection again
        if it failed show an error message
        :param path: the path written to
        :param tree: the tree we were trying to write
        :param tree: tree we were trying to write
        :param success: if writing succeeded or not
        """
        # update the collection
        if success:
            view.windows.Dialogs.message_box("Success", 'Tree written successfully!')
            self.open_collection_signal.emit()
        else:
            view.windows.Dialogs.error_box("ERROR", 'There were errors while writing the tree to ' + path + ','
                                                    ' for more details read the logs!')

    @pyqtSlot(dict)
    def open_node_types_finished(self, node_types: Dict[str, List[List[str]]]):
        """
        Method that handles the result of opening node types
        initializes the node types in the view
        :param node_types: the returned dictionary
        """
        self.gui.node_types_widget.set_up_node_types(node_types)
