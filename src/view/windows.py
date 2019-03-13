import re

from functools import partial
from pathlib import Path
from typing import List, Dict, Union

from PyQt5.QtWidgets import QAction, QMainWindow, QFileDialog, QMessageBox, QInputDialog, QLineEdit, QWidget, \
    QHBoxLayout

from model.config import Settings
from model.tree import Tree
from view.listeners import MainListener
from view.widget.tree_view_widget import TreeViewWidget
from view.widgets import NodeTypesWidget


class MainWindow(QMainWindow):
    """
    Class to draw the main window of the editor
    """

    def __init__(self):
        """
        Constructor for the main widget
        """
        super().__init__()

        # create listener that interacts with the controller workers
        self.main_listener = MainListener(self)

        self.def_window_title = 'RoboTeam Behaviour Tree Editor V2'
        self.setWindowTitle(self.def_window_title)

        # create a main widget with a HBoxLayout for each widget
        self.main_widget = QWidget()
        self.setMinimumHeight(800)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # widget with node types selector
        self.node_types_widget: NodeTypesWidget = NodeTypesWidget(self)
        # set margins of widget to 0, to prevent double margins
        self.node_types_widget.layout.setContentsMargins(0, 0, 0, 0)
        self.node_types_widget.setMinimumWidth(200)
        self.main_layout.addWidget(self.node_types_widget)

        # widget with the view of the tree
        self.tree_view_widget: TreeViewWidget = TreeViewWidget()
        self.tree_view_widget.layout.setContentsMargins(0, 0, 0, 0)
        self.tree_view_widget.setMinimumWidth(1000)
        self.main_layout.addWidget(self.tree_view_widget)

        # tree that has been loaded from the collection. USed for checking for unsaved changes
        self.load_tree = None
        # details about the tree currently shown
        # at start no tree is shown
        self.tree = None
        self.filename = None
        self.category = None

        # create a menubar instance
        self.menubar = MenuBar(self)
        self.menubar.build_menu_bar()

        # call to collection to create a collection from the default path
        # which initializes the menu bar
        self.menubar.open_collection()

    def enable_tree_actions(self, enable: bool=True):
        """
        these items are enabled if a tree is shown
        otherwise disabled
        :param enable: enable or not
        """
        self.menubar.close_tree_act.setEnabled(enable)
        self.menubar.save_tree_act.setEnabled(enable)
        self.menubar.save_tree_as_act.setEnabled(enable)
        self.tree_view_widget.toolbar.setEnabled(enable)

    def close_tree(self):
        """
        Closes the tree that currently is displayed
        """
        self.check_unsaved_changes()
        self.load_tree = None
        self.tree = None
        self.category = None
        self.filename = None
        self.enable_tree_actions(False)
        self.tree_view_widget.graphics_scene.clear()
        # clear the pah of the tree from the window title
        self.setWindowTitle(self.def_window_title)

    def show_tree(self, category, filename, tree):
        """
        Shows a tree
        :param category: category
        :param filename: filename
        :param tree: tree object to display
        """
        self.category = category
        self.tree = tree
        self.filename = filename
        self.enable_tree_actions(True)
        self.tree_view_widget.graphics_scene.add_tree(tree)
        # set the window title to also show the path of the tree
        self.setWindowTitle(self.def_window_title + ' - ' + self.category + '/' + self.filename)

    def check_unsaved_changes(self):
        if self.load_tree != self.tree:
            save = Dialogs.yes_no_message_box('Unsaved changes',
                                              'There are some unsaved changes, do you want to save them?')
            if save:
                self.main_listener.write_tree_signal.emit(self.category, self.filename, self.tree)


class MenuBar:
    """
    Class for initializing the menubar in the main window
    In a separate class for readability
    """
    def __init__(self, main_window: MainWindow):
        self.main_window = main_window

        # the current collection dict with categories and filenames displayed in the menubar
        self.collection_dict = None

        # actions that are displayed in the menubar
        # editor actions
        self.settings_act = QAction('Settings', self.main_window)
        self.settings_act.setStatusTip('Change settings')
        self.settings_act.setEnabled(False)
        # todo shortcut and action
        # settings_act.setShortcut()

        self.exit_act = QAction('Exit', self.main_window)
        self.exit_act.setShortcut('Alt+F4')
        self.exit_act.setStatusTip('Exit application')
        self.exit_act.triggered.connect(self.main_window.close)

        # collection actions
        self.open_collection_act = QAction('Open', self.main_window)
        self.open_collection_act.setShortcut('Ctrl+O')
        self.open_collection_act.setStatusTip('Open JSOn files Collection folder')
        self.open_collection_act.triggered.connect(self.open_collection_custom_path)

        self.save_collection_as_act = QAction('Save as', self.main_window)
        # self.# save_collection_as_act.setShortcut()
        self.save_collection_as_act.setShortcut('Save current collection as')
        self.save_collection_as_act.triggered.connect(self.save_collection_as)

        # tree actions
        self.close_tree_act = QAction('Close', self.main_window)
        self.close_tree_act.setShortcut('Ctrl+Q')
        self.close_tree_act.setStatusTip('Close the current tree from the view')
        self.close_tree_act.triggered.connect(self.main_window.close_tree)

        self.save_tree_act = QAction('Save', self.main_window)
        self.save_tree_act.setShortcut('Ctrl+S')
        self.save_tree_act.setStatusTip('Save the current tree')
        self.save_tree_act.triggered.connect(self.save_tree)

        self.save_tree_as_act = QAction('Save as', self.main_window)
        self.save_tree_as_act.setShortcut('Ctrl+Shift+S')
        self.save_tree_as_act.setStatusTip('Save the current tree as')
        self.save_tree_as_act.triggered.connect(self.save_tree_as)

    def build_menu_bar(self, collection_dict: Dict[str, List[str]]=None):
        """
        Reinitialized the menubar with a collection dict containing categories and filenames
        :param collection_dict: collection dict containing categories and filenames
        """
        self.collection_dict = collection_dict

        # clears the current menubar
        menubar = self.main_window.menuBar()
        menubar.clear()

        # creates an editor menu
        editor_menu = menubar.addMenu('&Editor')
        editor_menu.addAction(self.settings_act)
        editor_menu.addAction(self.exit_act)

        # creates a collection menu
        collection_menu = menubar.addMenu('&Collection')
        collection_menu.addAction(self.open_collection_act)
        collection_menu.addAction(self.save_collection_as_act)

        # creates a tree menu
        tree_menu = menubar.addMenu('&Tree')
        tree_menu.addAction(self.close_tree_act)
        tree_menu.addAction(self.save_tree_act)
        tree_menu.addAction(self.save_tree_as_act)

        # enable tree actions if a tree is displayed, disable if not
        if self.main_window.tree is not None:
            self.main_window.enable_tree_actions(True)
        else:
            self.main_window.enable_tree_actions(False)

        # initializes the collection menus and trees
        if not (collection_dict is None or len(collection_dict.keys()) == 0):
            for category, filenames in sorted(collection_dict.items()):
                # create a menu for the category
                # upper case first character of category
                category_upper: str = category[0].upper() + category[1:]
                category_menu = menubar.addMenu('&' + category_upper)

                # create the correct singular of the category
                category_singular = category_upper
                if category_singular.endswith('ies'):
                    category_singular = category_upper[:-3]
                    category_singular += 'y'
                elif category_upper.endswith('s'):
                    category_singular = category_upper[:-1]

                # add an action to the menu for creating a new tree with the singular of category
                add_tree_act = QAction('New ' + category_singular, self.main_window)
                add_tree_act.setStatusTip('Create a new ' + category_upper)
                add_tree_act.triggered.connect(partial(self.create_tree, category))
                # add_tree_act.setEnabled(False)
                category_menu.addAction(add_tree_act)
                # todo create action for making a new tree
                # adds an action for each file in the category
                for filename in filenames:
                    category_file_act = QAction(filename, self.main_window)
                    category_file_act.setStatusTip('Open ' + filename + ' in editor')
                    # displays a tree in main menu when selected
                    category_file_act.triggered.connect(partial(
                        self.open_tree_from_collection, category, filename))
                    category_menu.addAction(category_file_act)
        else:
            # if no collection was given,  display a disabled menu
            category_menu = menubar.addMenu('&No trees or directories were found')
            category_menu.setEnabled(False)

    def open_collection(self):
        """
        calls the emit signal for opening a collection
        :return:
        """
        self.main_window.main_listener.open_collection_signal.emit()

    def open_collection_custom_path(self):
        """
        Displays a folder selector
        Calls the emit signal for opening a collection
            if a folder is selected, otherwise nothing happens (cancel)
        """
        json_path = Settings.default_json_folder()
        path = Dialogs.select_folder('Open collection folder', json_path)
        # do a call to the controller to open the collection
        if path is not None:
            self.main_window.main_listener.open_collection_custom_path_signal.emit(path)

    def save_collection(self):
        """
        emits a signal to write the collection to the default path
        """
        self.main_window.main_listener.write_collection_signal.emit()

    def save_collection_as(self):
        """
        Emits a signal to write the collection to a custom path
        Custom path selected from folder selector
        """
        json_path = Settings.default_json_folder()
        path = Dialogs.select_folder('Save collection folder', json_path)
        # do a call to the controller to write the collection
        if path is not None:
            self.main_window.main_listener.write_collection_custom_path_signal.emit(path)

    def open_tree_from_collection(self, category: str, filename: str):
        """
        Emit signal to open tree from collection
        :param category: the category of the tree
        :param filename: the filename of the tree
        """
        self.main_window.main_listener.open_tree_from_collection_signal.emit(category, filename)

    def save_tree(self):
        """
        Save the tree currently displayed to the collection
        """
        self.main_window.main_listener.write_tree_signal.emit(self.main_window.category, self.main_window.filename,
                                                              self.main_window.tree)

    def save_tree_as(self):
        """
        Saves the tree currently displayed to a custom directory
        selected by a file save selector
        nothing happens when cancel is pressed
        """
        json_path = Settings.default_json_folder() / self.main_window.category
        path = Dialogs.save_file_dialog('Save tree as', self.main_window.filename, json_path)
        # do a call to the controller to write the collection
        if path is not None:
            self.main_window.main_listener.write_tree_custom_path_signal.emit(path, self.main_window.tree)

    def create_tree(self, category: str):
        self.main_window.check_unsaved_changes()
        name = Dialogs.text_input_dialog('Choose Tree name', 'Choose a name for the tree', "[A-Za-z0-9_+-]+")
        if name is None:
            return
        else:
            filename = name + '.json'
            tree = Tree(name, '')
            self.main_window.show_tree(category, filename, tree)


class Dialogs:
    @staticmethod
    def message_box(title: str, text: str):
        """
        Displays a message box with a title and message with only an ok button
        :param title: the title in the top bar
        :param text: the text in the message box
        """
        QMessageBox.question(None, title, text, QMessageBox.Ok, QMessageBox.Ok)

    @staticmethod
    def yes_no_message_box(title: str, text: str) -> bool:
        """
        Displays a message box with a title and message with yes no buttons
        :param title: the title in the top bar
        :param text: the text in the message box
        :return true if yes is clicked else false
        """
        clicked = QMessageBox.question(None, title, text, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        return True if clicked == QMessageBox.Yes else False

    @staticmethod
    def error_box(title: str, text: str):
        """
        Displays an error box with a title and message and only an ok button
        :param title: title in top bar
        :param text: text in the error box
        """
        button_reply = QMessageBox.critical(None, title, text, QMessageBox.Ok, QMessageBox.Ok)

    @staticmethod
    def select_folder(title: str, start_path: Path) -> Union[Path, None]:
        """
        Opens a folder selector to select a folder
        if cancel is pressed None will be returned otherwise a valid path
        :param title: the text in the top bar
        :param start_path: the path that the dialog will show when opened
        :return: None if cancel is pressed or a valid path
        """
        path = QFileDialog.getExistingDirectory(None, title, str(start_path), QFileDialog.ShowDirsOnly)
        # do nothing if cancel has been pressed
        if path is None or path == '':
            return None
        return Path(path)

    @staticmethod
    def save_file_dialog(title: str, name: str, start_path: Path) -> Union[Path, None]:
        """
        Opens a file save selector to select a save file location
        if cancel is pressed None will be returned otherwise a valid path
        :param title: the text in the top bar
        :param name: filename that will be selected if it exists
        :param start_path: the path that the dialog will show when opened
        :return: None if cancel is pressed or a valid path
        """
        path, _ = QFileDialog.getSaveFileName(None, title, str(start_path / name), "JSON files (*.json)")
        # do nothing if cancel has been pressed
        if path is None or path == '':
            return None
        return Path(path)

    @staticmethod
    def text_input_dialog(title: str, text: str, regex: str=None) -> Union[str, None]:
        """
        Creates an input dialog for a sting. Optional regex validation. If regex fails, keep asking for new input
        :param title: title at top bar
        :param text: text in message box
        :param regex: the regex to match
        :return: string if valid input is given, else None
        """
        string, ok_pressed = QInputDialog.getText(None, title, text, QLineEdit.Normal, "")
        if ok_pressed and string != '':
            if regex is not None:
                if not re.match(regex, string):
                    Dialogs.error_box("ERROR", "Invalid input given. Input should match pattern: " + regex)
                    return Dialogs.text_input_dialog(title, text, regex)
            return str(string)
        return None