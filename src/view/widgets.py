from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QPushButton

from model.config.node_types import NodeTypes
from model.config.settings import Settings


class NodeTypesWidget(QWidget):
    def __init__(self, gui):
        super(QWidget, self).__init__()
        self.gui = gui

        # vertical layout to align the widget and buttons
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # create the widget to display the node types
        self.node_types_widget = QTreeWidget()
        self.layout.addWidget(self.node_types_widget)

        # button to create a node type from the selected node type
        self.node_from_type_button = QPushButton('Create selected Type', self)
        self.node_from_type_button.setEnabled(False)
        self.layout.addWidget(self.node_from_type_button)

        # button for creating a new custom node type
        self.create_node_button = QPushButton('New Node', self)
        self.create_node_button.setEnabled(False)
        self.layout.addWidget(self.create_node_button)

        self.header = QTreeWidgetItem(["Node Types"])
        self.selected = None

        # emit signal to worker
        self.gui.main_listener.open_node_types_signal.emit()

    def set_up_node_types(self, node_types: Dict[str, List[List[str]]]=None):
        """
        Initializes the node types and shows them in a widget
        :param node_types: node types dictionary
        """
        self.node_types_widget.clear()
        self.node_types_widget.setHeaderItem(self.header)
        root = self.node_types_widget.invisibleRootItem()

        if node_types is None:
            path = Settings.default_node_types_folder()
            types_object = NodeTypes.from_csv(path)
            node_types = types_object.node_types

        for category, types in sorted(node_types.items()):
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
        # todo implement
        pass

    def node_from_selected_type(self):
        # todo implement
        pass
