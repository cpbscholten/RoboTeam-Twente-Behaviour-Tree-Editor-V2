from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QPushButton, QDialog, QFormLayout, \
    QLabel, QComboBox

from controller.utils import singularize, capitalize
from model.tree import NodeTypes, Node
from model.config import Settings
import view.windows


class NodeTypesWidget(QWidget):
    def __init__(self, gui):
        super(QWidget, self).__init__()
        self.gui: view.windows.MainWindow = gui

        # vertical layout to align the widget and buttons
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # create the widget to display the node types
        self.node_types_widget = QTreeWidget()
        self.layout.addWidget(self.node_types_widget)

        # button to create a node type from the selected node type
        self.node_from_type_button = QPushButton('Create selected Type', self)
        self.node_from_type_button.clicked.connect(self.node_from_selected_type)
        self.node_from_type_button.setEnabled(False)
        self.layout.addWidget(self.node_from_type_button)

        # button for creating a new custom node type
        self.create_node_button = QPushButton('New Node', self)
        self.create_node_button.clicked.connect(self.create_node_button_clicked)
        self.layout.addWidget(self.create_node_button)

        # button for adding a subtree
        self.add_subtree_button = QPushButton('Add subtree', self)
        self.add_subtree_button.clicked.connect(self.add_subtree_button_clicked)
        self.layout.addWidget(self.add_subtree_button)

        self.header = QTreeWidgetItem(["Node Types"])
        self.selected: QTreeWidgetItem = None

        # emit signal to worker
        self.gui.main_listener.open_node_types_signal.emit()

    def set_up_node_types(self, node_types: NodeTypes=None):
        """
        Initializes the node types and shows them in a widget
        :param node_types: node types dictionary
        """
        self.selected = None
        self.node_types_widget.clear()
        self.node_types_widget.setHeaderItem(self.header)
        root = self.node_types_widget.invisibleRootItem()

        if node_types is None:
            path = Settings.default_node_types_folder()
            node_types = NodeTypes.from_csv(path)

        for category, types in sorted(node_types.node_types.items()):
            category = QTreeWidgetItem(root, [category])
            for node_type in sorted(types):
                type_item = QTreeWidgetItem(category, [node_type[0]])
                # store the category and node type in the item
                type_item.setData(0, Qt.UserRole, category)
                type_item.setData(1, Qt.UserRole, node_type)
                # create children for each property and display set them to disabled
                for type_property in node_type[1:]:
                    property_item = QTreeWidgetItem(type_item, [type_property])
                    property_item.setDisabled(True)

        # disable edit triggers
        self.node_types_widget.setEditTriggers(self.node_types_widget.NoEditTriggers)

        # set up triggers
        self.node_types_widget.currentItemChanged.connect(self.node_type_selected)
        self.node_types_widget.itemDoubleClicked.connect(self.node_from_selected_type)

    def node_type_selected(self, current: QTreeWidgetItem):
        """
        Slot that handles when another node type is selected
        :param current: the current item selected in the TreeWidget
        """
        # check if the item is a node type
        if current.data(1, Qt.UserRole) is None:
            self.selected = None
            self.node_from_type_button.setEnabled(False)
        else:
            self.node_from_type_button.setEnabled(True)
            self.selected = current

    def create_node_button_clicked(self):
        """
        pyqtSlot that creates a new node by asking for a title and adds it to the view
        """
        title = view.windows.Dialogs.text_input_dialog("Create Node", "Title of the node:")
        if title is not None or '':
            print("test")
            node = Node(title)
            # todo add node to view

    def node_from_selected_type(self):
        """
        pyqtSlot for adding a node from the selected node types to the view
        """
        if self.selected is None:
            return
        node_type = self.selected.data(1, Qt.UserRole)
        node = NodeTypes.create_node_from_node_type(node_type)
        # todo use add created node to tree

    def add_subtree_button_clicked(self):
        """
        pyqtSlot for adding a subtree to the view by selecting the tree in a dialog
        """
        dialog = view.windows.TreeSelectDialog(self.gui.load_collection)
        category, filename = dialog.show()
        if category is None or filename is None:
            return
        tree = self.gui.load_collection.collection.get(category).get(filename)
        category_singular = singularize(capitalize(category))
        node = Node(tree.title, attributes={"name": category_singular})
        # todo add node to view
