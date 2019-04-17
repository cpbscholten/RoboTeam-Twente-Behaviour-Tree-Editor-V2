import json
import logging
from functools import partial

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QMimeData
from PyQt5.QtGui import QIcon, QPainter, QPalette, QKeySequence, QDrag
from PyQt5.QtWidgets import QGraphicsView, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QPushButton, QLabel, \
    QLineEdit, QFormLayout, QApplication, QGridLayout, QHBoxLayout, QComboBox, QAction, QAbstractItemView

import view.windows
import view.scenes
import view.elements
from controller.utils import singularize, capitalize
from model.tree import NodeTypes, Node

from typing import Dict, Any, Tuple


class NodeTreeWidget(QTreeWidget):

    def __init__(self, parent=None):
        super(NodeTreeWidget, self).__init__(parent=parent)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)

    def mimeData(self, items, _=None):
        if items:
            item = items[0]
            node_type = item.data(1, Qt.UserRole)
            if node_type:
                data = QMimeData()
                data.setText(json.dumps(node_type))
                return data
        return

    def startDrag(self, supported_actions):
        drag = QDrag(self)
        data = QMimeData()
        if self.selectedItems():
            item = self.selectedItems()[0]
            node_type = item.data(1, Qt.UserRole)
            if node_type:
                data.setText(json.dumps(node_type))
        drag.setMimeData(data)
        drag.exec(supported_actions)


class NodeTypesWidget(QWidget):

    # noinspection PyArgumentList
    def __init__(self, gui):
        super(QWidget, self).__init__()
        self.gui: view.windows.MainWindow = gui
        self.app: QApplication = self.gui.app
        # vertical layout to align the widget and buttons
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # create the widget to display the node types
        self.node_types_widget = NodeTreeWidget()
        self.layout.addWidget(self.node_types_widget)

        # button to create a node type from the selected node type
        self.node_from_type_button = QPushButton('Create selected Type', self)
        self.node_from_type_button.setShortcut('Ctrl+T')
        self.node_from_type_button.setToolTip('Create a node from the selected node type. Shortcut: Ctrl+T')
        self.node_from_type_button.clicked.connect(self.node_from_selected_type)
        self.node_from_type_button.setEnabled(False)
        self.layout.addWidget(self.node_from_type_button)

        # button for creating a new custom node type
        self.create_node_button = QPushButton('New Node', self)
        self.create_node_button.setShortcut('Ctrl+N')
        self.create_node_button.setToolTip('Create a new custom node. Shortcut: Ctrl+N')
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
        if not current.data(1, Qt.UserRole):
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
        if title or '':
            node = Node(title)
            self.add_node_to_view(node)
            # todo correctly display subtree

    def node_from_selected_type(self):
        """
        pyqtSlot for adding a node from the selected node types to the view
        """
        if not self.selected:
            return
        node_type = self.selected.data(1, Qt.UserRole)
        node = NodeTypes.create_node_from_node_type(node_type)
        self.add_node_to_view(node)

    def add_subtree_button_clicked(self):
        """
        pyqtSlot for adding a subtree to the view by selecting the tree in a dialog
        """
        dialog = view.windows.TreeSelectDialog(self.gui.collection)
        category, filename = dialog.show()
        if not (category or filename):
            return
        tree = self.gui.collection.collection.get(category).get(filename)
        category_singular = singularize(capitalize(category))
        node = Node(category_singular, attributes={"name": tree.name})
        # special case for rules, which are defined differently as subtrees as other trees
        if category_singular == 'Role':
            node.attributes['properties'] = {'ROLE': tree.name}
            node.attributes['role'] = tree.name
            self.add_node_to_view(node)
            self.gui.tree.add_subtree(self.gui.collection.collection.get('roles').get(filename), node.id)
        else:
            self.add_node_to_view(node)

    def add_node_to_view(self, node):
        # transfer new node to the scene
        scene = self.gui.tree_view_widget.graphics_scene
        # setting this attribute starts node addition sequence in the scene
        scene.adding_node = node
        self.gui.tree.add_node(node)
        # set special cursor for node addition
        self.app.add_cross_cursor(scene)


class TreeViewToolbar(QWidget):

    # noinspection PyArgumentList
    def __init__(self, scene, parent=None):
        """
        The constructor for a tree view toolbar
        :param scene: The tree scene for this toolbar
        :param parent: The parent widget
        """
        super(TreeViewToolbar, self).__init__(parent, Qt.Widget)
        self.scene = scene
        self.layout = QVBoxLayout(self)

        self.zoom_in_button = view.elements.ToolbarButton(QIcon("view/icon/plus.svg"))
        self.zoom_in_button.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_action = QAction()
        self.zoom_in_action.setShortcuts([QKeySequence.ZoomIn, QKeySequence(Qt.CTRL + Qt.Key_Equal)])
        self.zoom_in_action.triggered.connect(self.zoom_in_button.animateClick)
        self.zoom_in_button.addAction(self.zoom_in_action)
        self.zoom_in_button.clicked.connect(lambda: self.scene.zoom(1.25, 1.25))

        self.zoom_out_button = view.elements.ToolbarButton(QIcon("view/icon/minus.svg"))
        self.zoom_out_button.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_button.setShortcut(QKeySequence.ZoomOut)
        self.zoom_out_button.clicked.connect(lambda: self.scene.zoom(0.75, 0.75))

        self.reset_button = view.elements.ToolbarButton(QIcon("view/icon/refresh-cw.svg"))
        self.reset_button.setToolTip("Reset View (F5)")
        self.reset_action = QAction()
        self.reset_action.setShortcuts([QKeySequence.Refresh, QKeySequence(Qt.CTRL + Qt.Key_R)])
        self.reset_action.triggered.connect(self.reset_button.animateClick)
        self.reset_button.addAction(self.reset_action)
        self.reset_button.clicked.connect(self.scene.align_tree)

        self.layout.addWidget(self.zoom_in_button)
        self.layout.addWidget(self.zoom_out_button)
        self.layout.addWidget(self.reset_button)
        self.setLayout(self.layout)
        self.setGeometry(10, 10, self.layout.sizeHint().width(), self.layout.sizeHint().height())


class TreeViewWidget(QWidget):

    # noinspection PyArgumentList
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
        if self.property_display:
            self.property_display.resize()

    def remove_property_display(self):
        """
        Method to remove property display widget
        """
        if self.property_display:
            self.property_display.setParent(None)
            self.property_display.deleteLater()
            self.property_display = None

    def remove_tree(self):
        """
        clears tree from the widget and also the property display
        """
        self.graphics_scene.clear()
        self.remove_property_display()


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

    # noinspection PyArgumentList
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

    # noinspection PyArgumentList
    def __init__(self, gui):
        super(ToolbarWidget, self).__init__()
        self.gui = gui
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # overlay dropdown box
        self.view_label = QLabel("View:")
        self.view_dropdown = QComboBox()
        self.view_dropdown.addItems(["Overview", "Info View", "Heatmap - Success", "Heatmap - Waiting",
                                     "Heatmap - Running", "Heatmap - Failure"])
        # noinspection PyUnresolvedReferences
        self.view_dropdown.currentTextChanged[str].connect(self.switch_views)
        self.layout.addWidget(self.view_label)
        self.layout.addWidget(self.view_dropdown)
        self.layout.addStretch(1)
        # dropdown shortcuts
        self.overview_action = QAction('Overview', self.view_dropdown)
        self.overview_action.triggered.connect(lambda: self.view_dropdown.setCurrentIndex(0))
        self.overview_action.setShortcut('F1')
        self.view_dropdown.addAction(self.overview_action)
        self.info_view_action = QAction('Info View', self.view_dropdown)
        self.info_view_action.triggered.connect(lambda: self.view_dropdown.setCurrentIndex(1))
        self.info_view_action.setShortcut('F2')
        self.view_dropdown.addAction(self.info_view_action)
        self.heatmap_success_action = QAction('Heatmap - Success', self.view_dropdown)
        self.heatmap_success_action.triggered.connect(lambda: self.view_dropdown.setCurrentIndex(2))
        self.heatmap_success_action.setShortcut('F6')
        self.view_dropdown.addAction(self.heatmap_success_action)
        self.heatmap_waiting_action = QAction('Heatmap - Waiting', self.view_dropdown)
        self.heatmap_waiting_action.triggered.connect(lambda: self.view_dropdown.setCurrentIndex(3))
        self.heatmap_waiting_action.setShortcut('F7')
        self.view_dropdown.addAction(self.heatmap_waiting_action)
        self.heatmap_running_action = QAction('Heatmap - Running', self.view_dropdown)
        self.heatmap_running_action.triggered.connect(lambda: self.view_dropdown.setCurrentIndex(4))
        self.heatmap_running_action.setShortcut('F8')
        self.view_dropdown.addAction(self.heatmap_running_action)
        self.heatmap_failure_action = QAction('Heatmap - Failure', self.view_dropdown)
        self.heatmap_failure_action.triggered.connect(lambda: self.view_dropdown.setCurrentIndex(5))
        self.heatmap_failure_action.setShortcut('F9')
        self.view_dropdown.addAction(self.heatmap_failure_action)

        self.check_icon = QIcon('view/icon/check_green.svg')
        self.cross_icon = QIcon('view/icon/x_red.svg')

        self.check_or_cross = QPushButton()
        self.check_or_cross.setFlat(True)
        self.check_or_cross.setStyleSheet("QPushButton { border: none; margin: 0px; padding: 0px; }")
        self.check_or_cross.setIcon(self.check_icon)
        self.layout.addWidget(self.check_or_cross)

        # verification button
        self.verify_button = QPushButton("Verify")
        self.verify_button.setShortcut('Ctrl+E')
        self.verify_button.setToolTip('Verify the current tree. Shortcut: Ctrl+E')
        self.layout.addWidget(self.verify_button)
        self.verify_button.clicked.connect(partial(self.verify_tree, True))

    def enable_verify_button(self, enable: bool=True):
        """
        Enable or disable the verify button and checkmark icon
        :param enable: enable or disable
        """
        self.check_or_cross.setEnabled(enable)
        self.verify_button.setEnabled(enable)

    def switch_views(self, new_view: str):
        """
        Switch view to the new view specified by the combo box
        :param new_view: Selected view in the combo box
        """
        self.gui.tree_view_widget.graphics_scene.switch_info_mode(new_view == "Info View")
        if new_view.startswith("Heatmap"):
            self.gui.tree_view_widget.graphics_scene.simulator_mode = True
            if self.gui.tree:
                mode = new_view.split()[-1]
                signal = self.gui.main_listener.create_heatmap_signal
                timer = self.gui.main_listener.heatmap_timer
                if timer.isActive():
                    timer.stop()
                    timer = QTimer()
                    self.gui.main_listener.heatmap_timer = timer
                timer.timeout.connect(lambda: signal.emit(self.gui.tree.name, mode))
                timer.start(500)
        else:
            self.gui.tree_view_widget.graphics_scene.simulator_mode = False
            self.gui.main_listener.heatmap_timer.stop()

    def verify_tree(self, message: bool=False):
        """
        Slot that checks a tree when the verify button has been clicked
        :param message: If a dialog should be shown, or only update the checkmark
        """
        collection = self.gui.collection
        tree = self.gui.tree
        category = self.gui.category
        errors = collection.verify_tree(tree, category)

        # update check or cross icon
        if len(errors) == 0:
            self.check_or_cross.setIcon(self.check_icon)
            self.check_or_cross.setToolTip("No Errors were found during the last verification.")
        else:
            self.check_or_cross.setIcon(self.cross_icon)
            errors_tooltip = ["Errors during last verification run:"]
            errors_tooltip.extend(errors)
            self.check_or_cross.setToolTip('\n'.join(errors_tooltip))

        if message:
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
    logger = logging.getLogger('TreeViewPropertyDisplay')
    Y_OFFSET = 10
    X_OFFSET = 10

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

        # set enabled to false to prevent a flicker
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

        # Add buttons for saving and adding new properties and set some small margins so the buttons have space
        self.add_property_button = QPushButton("Add Property")
        self.add_property_button.clicked.connect(self.add_property)
        # Add property button in current row, 0th column, spanning 1 whole row
        self.layout.addWidget(self.add_property_button, self.layout.rowCount(), 0, 1, 0)

        # resize the widget, so it will be placed at the correct location
        self.resize()

        # show at the end before resizing to prevent a flicker
        self.show()

    def resize(self):
        """
        Method that correctly places the widget on the treeViewWidget
        """
        self.setGeometry(self.scene.view.width() - self.layout.sizeHint().width() - self.X_OFFSET, self.Y_OFFSET,
                         self.layout.sizeHint().width(), self.layout.sizeHint().height() + 25)

    def add_property(self):
        """
        Add a new property to our list
        :return: Nothing
        """
        root_window = self.scene.gui
        node_to_update = root_window.tree.nodes[self.node_id]
        self.update_properties()
        node_to_update.add_property("", "")
        updated_view = TreeViewPropertyDisplay(self.parent().graphics_scene, self.attributes,
                                               parent=self.parent(), node_id=self.node_id, node_title=self.node_title)
        if self.parent().property_display:
            self.setParent(None)
            self.deleteLater()
        self.scene.view.parent().property_display = updated_view

    def update_properties(self):
        """
        Update the properties of the node according to the properties in the property display window
        :return: True if success, False if the node of the property display does not exist anymore
        """
        root_window = self.scene.gui
        if self.node_id not in root_window.tree.nodes:
            return False
        node_to_update: Node = root_window.tree.nodes[self.node_id]
        properties = {}
        # Skip variable indicates if we're at the first entry of our rows or not.
        skip = False
        for item_index in range(0, self.layout.count()):
            if isinstance(self.layout.itemAt(item_index).widget(), QLineEdit):  # If it's an editable property
                if not skip:
                    skip = True
                    key = self.layout.itemAt(item_index).widget().text()
                    value = self.layout.itemAt(item_index + 1).widget().text()
                    if key in properties.keys():
                        TreeViewPropertyDisplay.logger.warning('There are two properties with key {}. '
                                                               'The first one will be stored.'.format(key))
                    properties[key] = value
                else:
                    skip = False
                    pass
        # remove empty line property
        if '' in properties.keys():
            properties.pop('')
        # optional propagate ROLE
        if "ROLE" in properties.keys():
            self.scene.gui.tree.propagate_role(self.node_id, properties.get("ROLE"))
        node_to_update.update_properties(properties)
        self.scene.nodes[self.node_id].model_node.attributes = node_to_update.attributes
        self.scene.gui.update_tree(self.scene.nodes[self.node_id].model_node)
        self.scene.nodes[self.node_id].initiate_view()
        return True

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
        if self.parent().property_display:
            self.setParent(None)
            self.deleteLater()
        self.scene.view.parent().property_display = updated_view

    def add_properties(self, attributes: Dict, node_id=None, title=None):
        """
        Show the properties of a node that was selected
        :param attributes: Attributes of selected node
        :param node_id: Id of the node
        :param title: Title of the node
        """
        # self.remove_rows()
        # Make dicts to be used to display attributes and properties in different ways
        display_attributes = dict()
        display_properties = dict()

        if node_id:
            display_attributes['id'] = node_id
        if title:
            display_attributes['title'] = title

        # Fill the attributes and properties dicts
        for key in attributes:
            if key != "properties":
                display_attributes[key] = attributes[key]
            else:
                for prop_key in attributes[key]:
                    display_properties[prop_key] = attributes[key][prop_key]

        # Add attributes to the display (these are non-editable)
        current_row = self.layout.rowCount()
        attributes_label = QLabel('Attributes')
        attributes_label.setStyleSheet('font-weight: bold')
        self.layout.addWidget(attributes_label, current_row, 0, 1, 0, Qt.AlignCenter)
        for key in display_attributes:
            current_row = self.layout.rowCount()
            key_label = QLabel(str(key))
            key_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label = QLabel(str(display_attributes[key]))
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.layout.addWidget(key_label, current_row, 0)
            self.layout.addWidget(value_label, current_row, 1)

        # Add property to the display (these are editable)
        current_row = self.layout.rowCount()
        properties_label = QLabel('Properties')
        properties_label.setStyleSheet('font-weight: bold')
        self.layout.addWidget(properties_label, current_row, 0, 1, 0, Qt.AlignCenter)
        for key in display_properties:
            current_row = self.layout.rowCount()
            key_line = QLineEdit(str(key))
            key_line.textChanged.connect(self.update_properties)
            value_line = QLineEdit(str(display_properties[key]))
            value_line.textChanged.connect(self.update_properties)
            remove_button = QPushButton(QIcon("view/icon/x.svg"), "", self)
            remove_button.setMinimumHeight(value_line.minimumHeight())
            remove_button.setStyleSheet("QPushButton {border: none; margin: 0px; padding: 0px;}")
            remove_button.setCursor(Qt.PointingHandCursor)
            remove_button.clicked.connect(partial(self.remove_property, key))
            self.layout.addWidget(key_line, current_row, 0)
            self.layout.addWidget(value_line, current_row, 1)
            self.layout.addWidget(remove_button, current_row, 2)
