from PyQt5.QtCore import pyqtSignal, Qt, QRectF, QPointF, QPoint
from PyQt5.QtGui import QPixmap, QFontMetrics, QBrush, QColor, QIcon
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsEllipseItem, QGraphicsScene, QGraphicsItem, \
    QGraphicsSimpleTextItem, QGraphicsLineItem, QPushButton

import view.widgets
from model.tree import Node as ModelNode, NodeTypes


class Node(QGraphicsEllipseItem):
    i = 0
    NODE_MIN_WIDTH = 100
    NODE_MAX_WIDTH = 150
    NODE_HEIGHT = 50
    NODE_COLOR = (152, 193, 217)                # LIGHT BLUE

    TACTIC_COLOR = (255, 51, 51)                # RED
    STRATEGY_COLOR = (77, 255, 77)              # GREEN
    ROLE_COLOR = (166, 77, 255)                 # PURPLE
    KEEPER_COLOR = (255, 255, 26)               # YELLOW
    OTHER_SUBTREE_COLOR = (147, 147, 147)       # GREY
    DECORATOR_COLOR = (51, 51, 255)             # DARK BLUE
    COMPOSITE_COLOR = (255, 153, 0)             # ORANGE
    OTHER_NODE_TYPES_COLOR = (255, 102, 153)    # PINK

    def __init__(self, x: float, y: float, scene: QGraphicsScene, model_node: ModelNode, title: str = None,
                 parent: QGraphicsItem = None, id: str= None, node_types: NodeTypes = None):
        """
        The constructor for a UI node
        :param x: x position for the center of the node
        :param y: y position for the center of the node
        :param title: title of the node displayed in the ui
        :param parent: parent of this graphics item
        """
        if title:
            self.title = title
        else:
            # give node a unique title
            self.title = "node {}".format(Node.i)
        self.id = id
        Node.i += 1
        self.scene = scene
        self.model_node = model_node
        self.children = []
        self.edges = []
        # store node position when collapsing upwards
        self.collapse_data = None
        # add node name label centered in the eclipse, elide if title is too long
        self.node_text = QGraphicsSimpleTextItem()
        metrics = QFontMetrics(self.node_text.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, self.NODE_MAX_WIDTH)
        self.node_text.setText(elided_title)
        self.node_text.setAcceptedMouseButtons(Qt.NoButton)
        self.node_text.setAcceptHoverEvents(False)
        text_width = self.node_text.boundingRect().width()
        text_height = self.node_text.boundingRect().height()
        self.node_text.setPos(x - (text_width / 2), y - (text_height / 2))
        # set node size based on text size
        if text_width > self.NODE_MIN_WIDTH - 10:
            rect = QRectF(x - (text_width + 10) / 2, y - self.NODE_HEIGHT / 2, text_width + 10, self.NODE_HEIGHT)
        else:
            rect = QRectF(x - self.NODE_MIN_WIDTH / 2, y - self.NODE_HEIGHT / 2, self.NODE_MIN_WIDTH, self.NODE_HEIGHT)
        # call super function now we know the node size
        super(Node, self).__init__(rect, parent)
        self.node_text.setParentItem(self)
        # indicates if node is being dragged
        self.dragging = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        # give the node a default colour
        self.setBrush(QBrush(QColor(*self.NODE_COLOR)))
        # give node another color
        if node_types is not None:
            # check for node types and color them
            types = node_types.get_node_type_by_name(model_node.title)
            if len(types) > 0:
                category, node_type = types[0]
                if category == 'decorators':
                    self.setBrush(QBrush(QColor(*self.DECORATOR_COLOR)))
                elif category == 'composites':
                    self.setBrush(QBrush(QColor(*self.COMPOSITE_COLOR)))
                else:
                    self.setBrush(QBrush(QColor(*self.OTHER_NODE_TYPES_COLOR)))
            # check for a strategy, role, tactic or keeper
            if 'name' in model_node.attributes.keys():
                if model_node.title == 'Tactic':
                    self.setBrush(QBrush(QColor(*self.TACTIC_COLOR)))
                elif model_node.title == 'Strategy':
                    self.setBrush(QBrush(QColor(*self.STRATEGY_COLOR)))
                elif model_node.title == 'Keeper':
                    self.setBrush(QBrush(QColor(*self.KEEPER_COLOR)))
                elif model_node.title == 'Role':
                    self.setBrush(QBrush(QColor(*self.ROLE_COLOR)))
                else:
                    self.setBrush(QBrush(QColor(*self.OTHER_SUBTREE_COLOR)))
        # create the bottom collapse/expand button for this node
        self.bottom_collapse_expand_button = CollapseExpandButton(self)
        self.bottom_collapse_expand_button.setParentItem(self)
        self.bottom_collapse_expand_button.setZValue(1)
        self.bottom_collapse_expand_button.collapse.connect(self.collapse_children)
        self.bottom_collapse_expand_button.expand.connect(self.expand_children)
        # position the bottom button at the bottom-center of the node
        button_x = x - (self.bottom_collapse_expand_button.boundingRect().width() / 2)
        button_y = y + (self.NODE_HEIGHT / 2) - (self.bottom_collapse_expand_button.boundingRect().height() / 2)
        self.bottom_collapse_expand_button.setPos(button_x, button_y)
        # hidden by default, the button is only needed if the node has children
        self.bottom_collapse_expand_button.hide()
        # create the top collapse/expand button for this node
        self.top_collapse_expand_button = CollapseExpandButton(self)
        self.top_collapse_expand_button.setParentItem(self)
        self.top_collapse_expand_button.setZValue(1)
        self.top_collapse_expand_button.collapse.connect(self.collapse_upwards)
        self.top_collapse_expand_button.expand.connect(self.expand_upwards)
        # position the top button at the top-center of the node
        button_x = x - (self.top_collapse_expand_button.boundingRect().width() / 2)
        button_y = y - (self.NODE_HEIGHT / 2) - (self.top_collapse_expand_button.boundingRect().height() / 2)
        self.top_collapse_expand_button.setPos(button_x, button_y)

    def add_child(self, child):
        """
        Add a child node
        Inheritance looks like: parent > edge > child
        :param child: Another ui node
        """
        edge = Edge(self, child)
        edge.setParentItem(self)
        # edge should stay behind the expand/collapse button
        edge.stackBefore(self.bottom_collapse_expand_button)
        self.children.append(child)
        self.edges.append(edge)
        # show the expand/collapse button when the first child is added
        if not self.bottom_collapse_expand_button.isVisible():
            self.bottom_collapse_expand_button.show()

    def moveBy(self, x, y):
        super(Node, self).moveBy(x, y)
        if self.parentItem() and isinstance(self.parentItem(), Edge):
            self.parentItem().change_position()

    def setPos(self, *args):
        super(Node, self).setPos(*args)
        if self.parentItem() and isinstance(self.parentItem(), Edge):
            self.parentItem().change_position()

    def xoffset(self):
        """
        recursively adds the relative x distances from this node up until the root node.
        :return: the sum of the relative x distances
        """
        if self.parentItem():
            return self.pos().x() + self.parentItem().xoffset()
        else:
            return self.pos().x() + self.rect().x() + self.rect().width() / 2

    def yoffset(self):
        """
        recursively adds the relative y distances from this node up until the root node.
        :return: the sum of the relative y distances
        """
        if self.parentItem():
            return self.pos().y() + self.parentItem().yoffset()
        else:
            return self.pos().y() + self.rect().y() + self.rect().height() / 2

    def xpos(self):
        """
        Calculates the x position of this node using the x offset
        :return: the x position of the node
        """
        return self.xoffset()

    def ypos(self):
        """
        Calculates the y position of this node using the y offset
        :return: the y position of the node
        """
        return self.yoffset()

    def collapse_upwards(self):
        """
        Collapses the tree upwards only displaying this node and its children
        :return:
        """
        # store collapse data used to restore the state when expanding
        self.collapse_data = {
            "abs_pos": (self.xpos(), self.ypos()),
            "rel_pos": self.pos(),
            "abs_top_level_pos": QPointF(self.topLevelItem().xoffset(), self.topLevelItem().yoffset()),
            "parent": self.parentItem(),
            "top_level_item": self.topLevelItem(),
            "root_item": self.scene.root_ui_node
        }
        # disconnect parent this prevents the node from being hidden
        self.setParentItem(None)
        # move node to retain correct position
        self.setPos(0, 0)
        self.moveBy(self.collapse_data["abs_pos"][0] - self.collapse_data["root_item"].xpos(),
                    self.collapse_data["abs_pos"][1] - self.collapse_data["root_item"].ypos())

        # hide parent nodes
        self.collapse_data['top_level_item'].hide()

    def expand_upwards(self):
        """
        Expands the tree upwards displaying all expanded parent nodes
        :return:
        """
        new_abs_pos = QPointF(self.xoffset(), self.yoffset())
        top_level_item = self.collapse_data['top_level_item']
        new_abs_top_level_pos = QPointF(top_level_item.xoffset(), top_level_item.yoffset())
        # reset parent item
        self.setParentItem(self.collapse_data['parent'])
        # reset relative position to parent
        self.setPos(self.collapse_data['rel_pos'] + (
                (new_abs_pos - QPointF(*self.collapse_data['abs_pos'])) -
                (new_abs_top_level_pos - self.collapse_data['abs_top_level_pos'])
            )
        )
        # show expanded parent nodes
        self.topLevelItem().show()

    def collapse_children(self):
        """
        Collapses this node's children by hiding all child edges (and therefore the whole subtree)
        """
        for c in self.childItems():
            if isinstance(c, Edge):
                c.hide()

    def expand_children(self):
        """
        Expands this node's children by showing all child edges previously hidden by the collapse function
        """
        for c in self.childItems():
            if isinstance(c, Edge):
                c.show()

    def sort_children(self):
        """
        Sort child edges/nodes based on x position
        :return: The model nodes in order
        """
        # gather all the edges
        child_edges = [edge for edge in self.childItems() if isinstance(edge, Edge)]
        # sort edges by x position of the child nodes
        child_edges.sort(key=lambda c: c.childItems()[0].xpos())
        # reset internal structure
        self.edges.clear()
        self.children.clear()
        # add children back in correct order
        for e in child_edges:
            e.setParentItem(None)
            self.edges.append(e)
            self.children.append(e.childItems()[0])
        # set the parent of the children in the correct order
        for e in child_edges:
            e.setParentItem(self)
        # return the model nodes in the correct order
        model_nodes_order = [e.childItems()[0].model_node for e in child_edges]
        return model_nodes_order

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on a node
        :param m_event: The mouse press event and its details
        """
        super(Node, self).mousePressEvent(m_event)
        tree = self.scene.gui.tree.nodes[self.id]
        if self.scene.view.parent().property_display is not None:
            self.scene.view.parent().property_display.update_properties()
            self.scene.view.parent().property_display.setParent(None)
            self.scene.view.parent().property_display.deleteLater()
        self.scene.view.parent().property_display = view.widgets.TreeViewPropertyDisplay(
            self.scene.view.parent().graphics_scene, tree.attributes, parent=self.scene.view.parent(), node_id=tree.id,
            node_title=tree.title)
        # TODO: Sort children when moving nodes and removes this function
        self.sort_children()

    def mouseMoveEvent(self, m_event):
        """
        Handles a mouse move over a node
        :param m_event: The mouse move event and its details
        """
        super(Node, self).mouseMoveEvent(m_event)
        if self.dragging:
            # move the node with the mouse and adjust the edges to the new position
            dx = m_event.scenePos().x() - m_event.lastScenePos().x()
            dy = m_event.scenePos().y() - m_event.lastScenePos().y()
            self.setPos(self.pos().x() + dx, self.pos().y() + dy)
            # reposition incoming edge
            if isinstance(self.parentItem(), Edge):
                self.parentItem().change_position()


class Edge(QGraphicsLineItem):

    def __init__(self, start_node, end_node):
        """
        The constructor for an ui edge
        :param start_node: Node on the start of the edge
        :param end_node: Node on the end of the edge
        """
        self.start_node = start_node
        self.end_node = end_node
        super(Edge, self).__init__(*self.get_position())
        end_node.setParentItem(self)

    def get_position(self):
        """
        Calculates the correct positions for both edge ends (keeps them connected to the nodes)
        :return: the start positions and end positions of the edge
        """
        # Position edge correctly, connecting the nodes
        start_x = self.start_node.rect().x() + (self.start_node.rect().width() / 2)
        start_y = self.start_node.rect().y() + self.start_node.rect().height()
        end_x = self.end_node.rect().x() + (self.end_node.rect().width() / 2) + self.end_node.pos().x()
        end_y = self.end_node.rect().y() + self.end_node.pos().y()
        return start_x, start_y, end_x, end_y

    def change_position(self):
        """
        Sets the edge to its correct position
        """
        self.setLine(*self.get_position())

    def xoffset(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the x offset of the parent
        """
        return self.parentItem().xoffset()

    def yoffset(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the y offset of the parent
        """
        return self.parentItem().yoffset()

    def xpos(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the x position of the parent
        """
        return self.parentItem().xpos()

    def ypos(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the y position of the parent
        """
        return self.parentItem().ypos()


class CollapseExpandButton(QGraphicsObject):

    collapse = pyqtSignal()
    expand = pyqtSignal()

    def __init__(self, parent):
        """
        The constructor of a collapse/expand button
        :param parent: The parent node where the button belongs to
        """
        self.node = parent
        # TODO: Use a global resource directory
        self.expand_icon = QPixmap("view/icon/expand.png")
        self.collapse_icon = QPixmap("view/icon/collapse.png")
        super(CollapseExpandButton, self).__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.isCollapsed = False

    def paint(self, painter, option, widget=None):
        if self.isCollapsed:
            painter.drawPixmap(0, 0, self.expand_icon)
        else:
            painter.drawPixmap(0, 0, self.collapse_icon)

    def boundingRect(self):
        return QRectF(0, 0, 9, 9)

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on the button: Change button icon and expand/collapse the node's children
        :param m_event: The mouse press event and its details
        """
        if self.isCollapsed:
            self.expand.emit()
            self.isCollapsed = False
        else:
            self.collapse.emit()
            self.isCollapsed = True


class ToolbarButton(QPushButton):

    def __init__(self, icon: QIcon):
        """
        The constructor for a toolbar button
        :param icon: The icon for this button
        """
        super(ToolbarButton, self).__init__(icon, "")
        self.setFixedSize(30, 30)
