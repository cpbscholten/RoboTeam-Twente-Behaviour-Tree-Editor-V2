from functools import partial

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPainter, QPalette
from PyQt5.QtWidgets import QGraphicsView, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QPushButton, QLabel, \
    QLineEdit, QFormLayout, QApplication, QGridLayout, QHBoxLayout

import view.windows
import view.scenes
import view.elements
from controller.utils import singularize, capitalize
from model.tree import NodeTypes, Node

from typing import Dict, Any, Tuple


class NodeTypesWidget(QWidget):
    def __init__(self, gui):
        super(QWidget, self).__init__()
        self.gui: view.windows.MainWindow = gui
        self.app: QApplication = self.gui.app
        # vertical layout to align the widget and buttons
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # create the widget to display the node types
        self.node_types_widget = QTreeWidget()
        self.layout.addWidget(self.node_types_widget)

        # button to create a node type from the selected node type
        self.node_from_type_button = QPushButton('Create selected Type', self)
        # todo fix shortcut node addition
        self.node_from_type_button.setShortcut('Ctrl+T')
        self.node_from_type_button.setToolTip('Create a node from the selected node type. Shortcut: Ctrl+T')
        self.node_from_type_button.clicked.connect(self.node_from_selected_type)
        self.node_from_type_button.setEnabled(False)
        self.layout.addWidget(self.node_from_type_button)

        # button for creating a new custom node type
        self.create_node_button = QPushButton('New Node', self)
        self.create_node_button.setShortcut('Ctrl+N')
        self.setToolTip('Create a new custom node. Shortcut: Ctrl+N')
        self.create_node_button.clicked.connect(self.create_node_button_clicked)
        self.layout.addWidget(self.create_node_button)

        # button for adding a subtree
        self.add_subtree_button = QPushButton('Add subtree', self)
        self.add_subtree_button.setShortcut('Ctrl+Shift+N')
        self.add_subtree_button.setToolTip('Create a subtree. Shortcut: Ctrl+Shift+N')
        self.add_subtree_button.clicked.connect(self.add_subtree_button_clicked)
        self.layout.addWidget(self.add_subtree_button)

        self.header = QTreeWidgetItem(["Node Types"])
        self.node_types_widget.setHeaderItem(self.header)

        self.selected: QTreeWidgetItem = None

        # disable edit triggers
        self.node_types_widget.setEditTriggers(self.node_types_widget.NoEditTriggers)

        # set up triggers
        self.node_types_widget.currentItemChanged.connect(self.node_type_selected)
        self.node_types_widget.itemDoubleClicked.connect(self.node_from_selected_type)

        # emit signal to worker
        self.gui.main_listener.open_node_types_signal.emit()

    def set_up_node_types(self, node_types: NodeTypes):
        """
        Initializes the node types and shows them in a widget
        :param node_types: node types dictionary
        """
        self.selected = None
        self.node_from_type_button.setEnabled(False)
        self.node_types_widget.clear()
        root = self.node_types_widget.invisibleRootItem()

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

    def node_type_selected(self, current: QTreeWidgetItem):
        """
        Slot that handles when another node type is selected
        :param current: the current item selected in the TreeWidget
        """
        # check for none to prevent errors when updating node types
        if not current or not self.gui.load_tree:
            return
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
        if self.app.wait_for_click_filter:
            self.app.wait_for_click_filter.reset_event_filter()
        title = view.windows.Dialogs.text_input_dialog("Create Node", "Title of the node:")
        if title is not None or '':
            node = Node(title)
            self.add_node_to_view(node)

    def node_from_selected_type(self):
        """
        pyqtSlot for adding a node from the selected node types to the view
        """
        if self.selected is None:
            return
        node_type = self.selected.data(1, Qt.UserRole)
        node = NodeTypes.create_node_from_node_type(node_type)
        self.add_node_to_view(node)

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
        node = Node(category_singular, attributes={"name": tree.name})
        self.add_node_to_view(node)

    def add_node_to_view(self, node):
        # transfer new node to the scene
        scene = self.gui.tree_view_widget.graphics_scene
        # setting this attribute starts node addition sequence in the scene
        scene.adding_node = node
        # set special cursor for node addition
        self.app.add_node_cursor(scene)


class TreeViewToolbar(QWidget):

    def __init__(self, scene, parent=None):
        """
        The constructor for a tree view toolbar
        :param scene: The tree scene for this toolbar
        :param parent: The parent widget
        """
        super(TreeViewToolbar, self).__init__(parent, Qt.Widget)
        self.scene = scene
        self.layout = QVBoxLayout(self)
        self.zoom_in_button = view.elements.ToolbarButton(QIcon("view/icon/zoom_in.svg"))
        self.zoom_in_button.clicked.connect(lambda: self.scene.zoom(1.25, 1.25))
        self.zoom_out_button = view.elements.ToolbarButton(QIcon("view/icon/zoom_out.svg"))
        self.zoom_out_button.clicked.connect(lambda: self.scene.zoom(0.75, 0.75))
        # self.filter_button = ToolbarButton(QIcon("view/icon/filter.svg"))
        self.reset_button = view.elements.ToolbarButton(QIcon("view/icon/reset.svg"))
        self.reset_button.clicked.connect(self.scene.align_tree)
        self.layout.addWidget(self.zoom_in_button)
        self.layout.addWidget(self.zoom_out_button)
        # self.layout.addWidget(self.filter_button)
        self.layout.addWidget(self.reset_button)
        self.setLayout(self.layout)
        self.setGeometry(10, 10, self.layout.sizeHint().width(), self.layout.sizeHint().height())


class TreeViewWidget(QWidget):

    def __init__(self, gui, parent: QWidget=None):
        """
        The constructor for a tree view widget
        :param gui the main window
        :param parent: The parent widget
        """
        super(TreeViewWidget, self).__init__(parent, Qt.Widget)
        self.gui = gui
        self.layout = QVBoxLayout(self)
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setCursor(Qt.OpenHandCursor)
        self.graphics_view.setRenderHints(QPainter.Antialiasing)
        self.graphics_scene = view.scenes.TreeScene(self.graphics_view, self.gui, self)
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setMinimumSize(500, 500)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.toolbar = TreeViewToolbar(self.graphics_scene, self)
        self.node_color_legend_widget = NodeColorLegendWidget(self.graphics_scene, self.gui.app, self)
        self.property_display: TreeViewPropertyDisplay = None
        self.layout.addWidget(self.graphics_view)
        self.setLayout(self.layout)

    def resizeEvent(self, resize_event):
        """
        Overrides the method when this widget is resized, to correctly place the widgets on the view
        :param resize_event: the old dimensions
        """
        self.node_color_legend_widget.resize()
        if self.property_display is not None:
            self.property_display.resize()


class NodeColorLegendWidget(QWidget):
    """
    Legend widget to show which color map to node type or category
    """
    Y_OFFSET = 10
    X_OFFSET = 10

    def __init__(self, scene, app: QApplication, parent=None):
        super(NodeColorLegendWidget, self).__init__(parent, Qt.Widget)
        self.scene = scene
        self.app = app
        self.parent = parent
        self.widget = None
        self.layout = None
        self.collapse_button = None
        self.expand_button = None
        self.expanded = False
        self.init()

    def set_expanded(self, expand: bool):
        """
        Removes the current legend and rebuild a collapsed or expanded version
        :param expand: if the widget should be expanded or collapsed
        """
        self.expanded = expand
        # delete the old legend
        self.widget.deleteLater()
        # initialize a collapsed or expanded version
        self.init()

    def init(self):
        """
        Rebuilds the legend based on the expanded variable
        """
        # creates a new widget and add it to the scene
        self.widget = QWidget()
        self.widget.setParent(self.parent)
        self.layout = QFormLayout()
        self.widget.setLayout(self.layout)
        self.widget.setAutoFillBackground(True)
        # set to correct system palette of the widget
        palette = self.palette()
        background = self.app.palette().brush(QPalette.Background).color()
        palette.setColor(self.backgroundRole(), background)
        self.widget.setPalette(palette)
        # initialize an expanded or collapsed widget
        if self.expanded:
            self.expand()
        else:
            self.collapse()
        # place the widget on the correct place on the screen
        self.resize()
        self.widget.show()

    def collapse(self):
        """
        Create a collapsed version of the widget. Can only be called through init()
        """
        self.expand_button = QPushButton()
        self.expand_button.setIcon(QIcon('view/icon/expand.png'))
        self.expand_button.setShortcut('Ctrl+L')
        self.expand_button.setToolTip('Expand the legend. Shortcut: Ctrl+L')
        self.expand_button.clicked.connect(partial(self.set_expanded, True))
        self.expand_button.setFlat(True)
        self.expand_button.setStyleSheet("QPushButton { border: none; margin: 0px; padding: 0px; }")
        self.layout.addRow(self.expand_button, QLabel("Legend"))

    def expand(self):
        """
        Create an expanded version of the legend. Can only be called through init()
        """
        self.collapse_button = QPushButton()
        self.collapse_button.setIcon(QIcon('view/icon/collapse.png'))
        self.collapse_button.setShortcut('Ctrl+L')
        self.collapse_button.setToolTip('Collapse the legend. Shortcut: Ctrl+L')
        self.collapse_button.clicked.connect(partial(self.set_expanded, False))
        self.collapse_button.setFlat(True)
        self.collapse_button.setStyleSheet("QPushButton { border: none; margin: 0px; padding: 0px; }")
        self.layout.addRow(self.collapse_button, QLabel("Legend"))
        self.layout.addRow(QLabel("Subtrees:"))
        self.add_legend_type("Keeper", view.elements.Node.KEEPER_COLOR)
        self.add_legend_type("Role", view.elements.Node.ROLE_COLOR)
        self.add_legend_type("Strategy", view.elements.Node.STRATEGY_COLOR)
        self.add_legend_type("Tactic", view.elements.Node.TACTIC_COLOR)
        self.add_legend_type("Other", view.elements.Node.OTHER_SUBTREE_COLOR)
        self.layout.addRow(QLabel("Node Types:"))
        self.add_legend_type("Composite", view.elements.Node.COMPOSITE_COLOR)
        self.add_legend_type("Decorator", view.elements.Node.DECORATOR_COLOR)
        self.add_legend_type("Other", view.elements.Node.OTHER_NODE_TYPES_COLOR)
        self.layout.addRow(QLabel("Other:"))
        self.add_legend_type("Other", view.elements.Node.NODE_COLOR)

    def resize(self):
        """
        Places the window at the bottom of the screen
        :return:
        """
        self.widget.setGeometry(self.X_OFFSET,
                                self.scene.view.height() - self.layout.sizeHint().height() - self.Y_OFFSET,
                                self.layout.sizeHint().width(), self.layout.sizeHint().height())

    def add_legend_type(self, title: str, rgb: Tuple[int, int, int]):
        """
        Helper method to add color types to the legend
        :param title: the name
        :param rgb: the color to display in rgb tuple
        """
        color_label = QLabel("●")
        color_label.setStyleSheet("QLabel { color: rgb" + str(rgb) + "; }")
        self.layout.addRow(color_label, QLabel(title))


class ToolbarWidget(QWidget):
    """
    Widget with a button toolbar for a verification button
    """

    def __init__(self, gui):
        super(ToolbarWidget, self).__init__()
        self.gui = gui
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.layout.addStretch(1)

        # verification button
        self.verify_button = QPushButton("Verify")
        self.verify_button.setShortcut('Ctrl+E')
        self.verify_button.setToolTip('Verify the current tree. Shortcut: Ctrl+E')
        self.layout.addWidget(self.verify_button)
        self.verify_button.clicked.connect(self.verify_tree)

    def verify_tree(self):
        """
        Slot that checks a tree when the verify button has been clicked
        """
        collection = self.gui.load_collection
        tree = self.gui.tree
        category = self.gui.category
        # TODO add checkmark
        errors = collection.verify_tree(tree, category)
        if len(errors) == 0:
            view.windows.Dialogs.message_box("Success", "The Tree has been verified successfully. "
                                             "No errors have been found.")
        else:
            view.windows.Dialogs.error_box("Error", "There were errors while verifying the tree, "
                                                    "click more details for more info.", errors)


class TreeViewPropertyDisplay(QWidget):
    """
    Widget for viewing and editing properties of a node
    """

    Y_OFFSET = 10
    X_OFFSET = 10
    ROW_MIN_HEIGHT = 25
    ROW_MIN_WIDTH = 100
    BUTTON_MARGINS = 6

    def __init__(self, scene, attributes: Dict[str, Any], parent=None, node_id=None, node_title=None):
        """
        The constructor for a tree view toolbar
        :param scene: The tree scene for this property display
        :param attributes: Attributes given to be displayed
        :param parent: The parent widget
        :param node_id: Id of the node to be displayed
        :param node_title: Title of the node to be displayed
        """
        super(TreeViewPropertyDisplay, self).__init__(parent, Qt.Widget)
        self.scene = scene
        self.layout = QGridLayout(self)
        self.attributes = attributes
        self.node_id = node_id
        self.node_title = node_title
        self.setLayout(self.layout)

        # Add attributes if given
        if attributes is not None:
            self.add_properties(attributes, node_id, node_title)

        self.setAutoFillBackground(True)
        palette = self.palette()
        background = QtWidgets.QApplication.instance().palette().brush(QPalette.Background).color()
        palette.setColor(self.backgroundRole(), background)
        self.setPalette(palette)
        self.show()

        # Add buttons for saving and adding new properties and set some small margins so the buttons have space
        self.add_property_button = QPushButton("Add Property")
        self.add_property_button.clicked.connect(self.add_property)
        self.add_property_button.setContentsMargins(self.BUTTON_MARGINS, self.BUTTON_MARGINS, self.BUTTON_MARGINS, self.BUTTON_MARGINS)

        # Add property button in current row, 0th column, spanning 1 row and 3 columns
        self.layout.addWidget(self.add_property_button, self.layout.rowCount(), 0, 1, 3)

        # resize the widget, so it will be placed at the correct location
        self.resize()

    def resize(self):
        """
        Method that correctly places the widget on the treeViewWidget
        """
        self.setGeometry(self.scene.view.width() - self.layout.sizeHint().width() - self.X_OFFSET, self.Y_OFFSET, self.layout.sizeHint().width(), self.layout.sizeHint().height())

    def add_property(self):
        """
        Add a new property to our list
        :return: Nothing
        """
        root_window = self.scene.gui
        node_to_update = root_window.tree.nodes[self.node_id]
        self.update_properties()
        node_to_update.add_property("", "")
        updated_view = TreeViewPropertyDisplay(self.parent().graphics_scene, self.attributes, parent=self.parent(), node_id=self.node_id, node_title=self.node_title)
        if self.parent().property_display is not None:
            self.setParent(None)
            self.deleteLater()
        self.scene.view.parent().property_display = updated_view

    def update_properties(self):
        """
        Update the properties of the node according to the properties in the property display window
        :return: Nothing
        """
        # TODO: Add logging if two entries have the same key
        properties = []
        # Skip variable indicates if we're at the first entry of our rows or not.
        skip = False
        for item_index in range(0, self.layout.count()):
            if isinstance(self.layout.itemAt(item_index).widget(), QLineEdit):  # If it's an editable property
                if not skip:
                    skip = True
                    properties.append((self.layout.itemAt(item_index).widget().text(), self.layout.itemAt(item_index + 1 ).widget().text()))
                else:
                    skip = False
                    pass
        root_window = self.scene.gui
        node_to_update = root_window.tree.nodes[self.node_id]
        if len(properties) > 0:
            node_to_update.attributes["properties"] = {}
            for node_property in properties:
                node_to_update.add_property(node_property[0], node_property[1])
                # If we have a ROLE property, propagate that to its children
                if node_property[0] == "ROLE":
                    self.propagate_role(self.node_id, node_property[1])

    def propagate_role(self, current_node_id: str, to_propagate: str):
        """
        Function to recursively go through children to propagate ROLE property.
        :param current_node_id: id of the current node.
        :param to_propagate: the value of the ROLE property to propagate
        """
        root_window = self.scene.gui
        children = root_window.tree.nodes[current_node_id].children
        for child in children:
            current_child = root_window.tree.nodes[child]
            current_child.add_property("ROLE", to_propagate)
            self.propagate_role(child, to_propagate)

    def remove_rows(self):
        """
        Remove all the rows in our QFormLayout
        """
        while self.layout.rowCount() > 0:
            self.layout.removeRow(0)

    def remove_property(self, key):
        """
        Remove property from properties that node has
        :param key: Key of the property
        """
        root_window = self.scene.gui
        node_to_update = root_window.tree.nodes[self.node_id]
        node_to_update.remove_property(key)
        updated_view = TreeViewPropertyDisplay(self.parent().graphics_scene, self.attributes, parent=self.parent(),
                                               node_id=self.node_id, node_title=self.node_title)
        if self.parent().property_display is not None:
            self.setParent(None)
            self.deleteLater()
        self.scene.view.parent().property_display = updated_view

    def add_properties(self, attributes: Dict, id=None, title=None):
        """
        Show the properties of a node that was selected
        :param attributes: Attributes of selected node
        :param id: Id of the node
        :param title: Title of the node
        """
        # self.remove_rows()
        # Make dicts to be used to display attributes and properties in different ways
        display_attributes = dict()
        display_properties = dict()

        if id is not None:
            display_attributes['id'] = id
        if title is not None:
            display_attributes['title'] = title

        # Fill the attributes and properties dicts
        for key in attributes:
            if key != "properties":
                display_attributes[key] = attributes[key]
            else:
                for prop_key in attributes[key]:
                    display_properties[prop_key] = attributes[key][prop_key]

        # Add attributes to the display (these are non-editable)
        # TODO: Add heading to say these are attributes?
        for key in display_attributes:
            current_row = self.layout.rowCount()
            key_label = QLabel(str(key))
            key_label.setMinimumSize(self.ROW_MIN_WIDTH, self.ROW_MIN_HEIGHT)
            value_label = QLabel(str(display_attributes[key]))
            value_label.setMinimumSize(self.ROW_MIN_WIDTH, self.ROW_MIN_HEIGHT)
            self.layout.addWidget(key_label, current_row, 0)
            self.layout.addWidget(value_label, current_row, 1)

        # Add property to the display (these are editable)
        # TODO: Add heading to say these are properties?
        for key in display_properties:
            current_row = self.layout.rowCount()
            key_line = QLineEdit(str(key))
            key_line.setMinimumSize(self.ROW_MIN_WIDTH, self.ROW_MIN_HEIGHT)
            value_line = QLineEdit(str(display_properties[key]))
            value_line.setMinimumSize(self.ROW_MIN_WIDTH, self.ROW_MIN_HEIGHT)
            remove_button = QPushButton(QIcon("view/icon/delete_icon.svg"), "", self)
            remove_button.clicked.connect(partial(self.remove_property, key))
            self.layout.addWidget(key_line, current_row, 0)
            self.layout.addWidget(value_line, current_row, 1)
            self.layout.addWidget(remove_button, current_row, 2)
