import logging

from PyQt5.QtCore import pyqtSignal, Qt, QRectF, QPointF, QRect
from PyQt5.QtGui import QPixmap, QFontMetrics, QBrush, QColor, QIcon, QPainter
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsScene, QGraphicsItem, \
    QGraphicsSimpleTextItem, QGraphicsLineItem, QPushButton, QMenu, QAction, QStyleOptionGraphicsItem, QGraphicsRectItem

import view.widgets
from model.tree import Node as ModelNode, NodeTypes


class Node(QGraphicsItem):
    logger = logging.getLogger('ViewNode')

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
    DEFAULT_SIMULATOR_COLOR = Qt.white

    def __init__(self, x: float, y: float, scene: QGraphicsScene, model_node: ModelNode, title: str = None,
                 parent: QGraphicsItem = None, node_types: NodeTypes = None):
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
        self.id = model_node.id
        self.x = x
        self.y = y
        Node.i += 1
        self.scene = scene
        self.model_node = model_node
        self.children = []
        self.edges = []
        # store node positional data when detaching from parent
        self.expand_data = None
        # add node name label centered in the eclipse, elide if title is too long
        self.node_text = QGraphicsSimpleTextItem()
        metrics = QFontMetrics(self.node_text.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, self.NODE_MAX_WIDTH)
        self.node_text.setText(elided_title)
        self.node_text.setAcceptedMouseButtons(Qt.NoButton)
        self.node_text.setAcceptHoverEvents(False)
        self.text_width = self.node_text.boundingRect().width()
        self.text_height = self.node_text.boundingRect().height()
        self.node_text.setX(x - (self.text_width / 2))
        # call super function now we know the node size
        super(Node, self).__init__(parent)
        self.node_text.setParentItem(self)
        # indicates if node is being dragged
        self.dragging = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        # give the node a default color
        self.brush = QBrush(QColor(*self.NODE_COLOR))
        self.simulator_brush = QBrush(self.DEFAULT_SIMULATOR_COLOR)
        # give node another color
        if node_types is not None:
            # check for node types and color them
            types = node_types.get_node_type_by_name(model_node.title)
            if len(types) > 0:
                category, node_type = types[0]
                if category == 'decorators':
                    self.brush.setColor(QColor(*self.DECORATOR_COLOR))
                elif category == 'composites':
                    self.brush.setColor(QColor(*self.COMPOSITE_COLOR))
                else:
                    self.brush.setColor(QColor(*self.OTHER_NODE_TYPES_COLOR))
            # check for a strategy, role, tactic or keeper
            if 'name' in model_node.attributes.keys() or 'role' in model_node.attributes.keys():
                if model_node.title == 'Tactic':
                    self.brush.setColor(QColor(*self.TACTIC_COLOR))
                elif model_node.title == 'Strategy':
                    self.brush.setColor(QColor(*self.STRATEGY_COLOR))
                elif model_node.title == 'Keeper':
                    self.brush.setColor(QColor(*self.KEEPER_COLOR))
                elif model_node.title == 'Role':
                    self.brush.setColor(QColor(*self.ROLE_COLOR))
                else:
                    self.brush.setColor(QColor(*self.OTHER_SUBTREE_COLOR))
        self.info_display = []
        self.max_width = 0
        self.total_height = 0
        self.bottom_collapse_expand_button = None
        self.top_collapse_expand_button = None
        self._rect = None
        self.initiate_view()

    def initiate_view(self, propagate=False):
        """
        Initiates all the children for the current view
        :param propagate: Propagate initiate view signal to children
        """
        for rect in self.info_display:
            rect.setParentItem(None)
        if self.top_collapse_expand_button and self.bottom_collapse_expand_button:
            self.top_collapse_expand_button.setParentItem(None)
            self.bottom_collapse_expand_button.setParentItem(None)
        self.info_display = []
        self.max_width = self.text_width
        self.total_height = self.NODE_HEIGHT
        if self.scene.info_mode:
            self.create_info_display(self.x, self.y, self.model_node.attributes)
        if self.max_width > self.NODE_MIN_WIDTH - 10:
            self._rect = QRect(self.x - self.max_width / 2, self.y - self.total_height / 2, self.max_width,
                               self.total_height)
        else:
            self._rect = QRect(self.x - self.NODE_MIN_WIDTH / 2, self.y - self.total_height / 2, self.NODE_MIN_WIDTH,
                               self.total_height)
        # set node size based on children
        self.node_text.setY(self.y - self.total_height / 2 + self.NODE_HEIGHT / 2 - self.text_height / 2)
        self.create_expand_collapse_buttons()
        self.scene.update()
        if propagate:
            for c in self.children:
                c.initiate_view(True)
            for e in self.edges:
                e.change_position()

    def create_expand_collapse_buttons(self):
        """
        Creates the expand/collapse buttons of the node
        """
        # create the bottom collapse/expand button for this node
        if self.bottom_collapse_expand_button:
            bottom_collapsed = self.bottom_collapse_expand_button.isCollapsed
        else:
            bottom_collapsed = False
        self.bottom_collapse_expand_button = CollapseExpandButton(self)
        self.bottom_collapse_expand_button.setParentItem(self)
        self.bottom_collapse_expand_button.collapse.connect(self.collapse_children)
        self.bottom_collapse_expand_button.expand.connect(self.expand_children)
        self.bottom_collapse_expand_button.isCollapsed = bottom_collapsed
        # position the bottom button at the bottom-center of the node
        button_x = self.x - (self.bottom_collapse_expand_button.boundingRect().width() / 2)
        button_y = self.y + self.total_height / 2 - (self.bottom_collapse_expand_button.boundingRect().height() / 2)
        self.bottom_collapse_expand_button.setPos(button_x, button_y)
        # hidden by default, the button is only needed if the node has children
        if not self.children:
            self.bottom_collapse_expand_button.hide()
        # create the top collapse/expand button for this node
        if self.top_collapse_expand_button:
            top_collapsed = self.top_collapse_expand_button.isCollapsed
        else:
            top_collapsed = False
        self.top_collapse_expand_button = CollapseExpandButton(self)
        self.top_collapse_expand_button.setParentItem(self)
        self.top_collapse_expand_button.collapse.connect(self.collapse_upwards)
        self.top_collapse_expand_button.expand.connect(self.expand_upwards)
        self.top_collapse_expand_button.isCollapsed = top_collapsed
        if self.scene.root_ui_node == self or self.scene.reconnecting_node == self:
            self.top_collapse_expand_button.hide()
        # position the top button at the top-center of the node
        button_x = self.x - (self.top_collapse_expand_button.boundingRect().width() / 2)
        button_y = self.y - self.total_height / 2 - (self.top_collapse_expand_button.boundingRect().height() / 2)
        self.top_collapse_expand_button.setPos(button_x, button_y)

    def create_info_display(self, x, y, attributes):
        """
        Creates view elements for the info display
        :param x: x position of the node
        :param y: y position of the node
        :param attributes: attributes that will be displayed in the view
        :return:
        """
        start_height = y + (self.NODE_HEIGHT / 2)
        # unfold dictionary values at the bottom of the list
        sorted_attributes = []
        for k, v in sorted(attributes.items(), key=lambda tup: isinstance(tup[1], dict)):
            if isinstance(v, dict):
                sorted_attributes.append((k, v))
                sorted_attributes.extend(v.items())
            else:
                sorted_attributes.append((k, v))
        # create property rows
        for i, (k, v) in enumerate(sorted_attributes):
            value_text = None
            value_height = 0
            if isinstance(v, dict):
                # display dictionary key as title
                text = "{}".format(k)
                if len(text) > 20:
                    text = text[:20] + "..."
                key_text = QGraphicsSimpleTextItem(text)
                f = key_text.font()
                f.setBold(True)
                key_text.setFont(f)
                text_width = key_text.boundingRect().width()
            else:
                key_text = QGraphicsSimpleTextItem("{}:".format(k) if k else " ")
                text = str(v)
                if len(text) > 20:
                    text = text[:20] + "..."
                value_text = QGraphicsSimpleTextItem(text)
                value_height = value_text.boundingRect().height()
                text_width = key_text.boundingRect().width() + value_text.boundingRect().width()
            # create box around property
            attribute_container = QGraphicsRectItem(x, start_height, text_width + 10,
                                                    max(key_text.boundingRect().height(),
                                                        value_height) + 10)
            attribute_container.setBrush(QBrush(Qt.white))
            self.total_height += attribute_container.rect().height()
            key_text.setParentItem(attribute_container)
            if value_text:
                value_text.setParentItem(attribute_container)
            self.max_width = max(self.max_width, attribute_container.rect().width())
            attribute_container.setParentItem(self)
            self.info_display.append(attribute_container)
            start_height += max(key_text.boundingRect().height(), value_height) + 10
        # calculate correct coordinates for positioning of the attribute boxes
        if self.max_width > self.NODE_MIN_WIDTH - 10:
            x -= (self.max_width + 10) / 2
            y -= self.total_height / 2
            self.max_width += 10
        else:
            x -= self.NODE_MIN_WIDTH / 2
            y -= self.total_height / 2
            self.max_width = self.NODE_MIN_WIDTH
        h = 0
        # position all the elements previously created
        for attribute_container in self.info_display:
            rect: QRectF = attribute_container.rect()
            rect.setX(x)
            rect_height = rect.height()
            rect.setY(y + self.NODE_HEIGHT + h)
            rect.setHeight(rect_height)
            key_child = attribute_container.childItems()[0]
            if len(attribute_container.childItems()) == 2:
                key_child.setX(x + 5)
                value_child = attribute_container.childItems()[1]
                value_child.setX(x + self.max_width - value_child.boundingRect().width() - 5)
                value_child.setY(y + self.NODE_HEIGHT + h + 5)
            else:
                key_child.setX(x - key_child.boundingRect().width() / 2 + self.max_width / 2)
            key_child.setY(y + self.NODE_HEIGHT + h + 5)
            h += rect.height()
            rect.setWidth(self.max_width)
            attribute_container.setRect(rect)

    def paint(self, painter: QPainter, style_options: QStyleOptionGraphicsItem, widget=None):
        """
        Paint the basic shape of the node (ellipse or rectangle)
        :param painter: painter used to paint objects
        :param style_options: Styling options for the graphics item
        :param widget: The widget being painted
        """
        painter.setPen(Qt.SolidLine)
        if self.scene.simulator_mode:
            brush = self.simulator_brush
        else:
            brush = self.brush
        painter.setBrush(brush)
        if self.scene.info_mode:
            painter.drawRect(self.rect().x(), self.rect().y(), self.rect().width(), self.NODE_HEIGHT)
        else:
            painter.drawEllipse(self.rect())

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
        if not child.top_collapse_expand_button.isVisible():
            child.top_collapse_expand_button.show()

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

    def boundingRect(self):
        return QRectF(self._rect)

    def rect(self):
        return self._rect

    def detach_from_parent(self):
        if not self.parentItem() or not self.parentItem().parentItem():
            Node.logger.error("The node can't detach from parent, no parent")
            return
        # store attach data used to restore the state when attaching
        xpos, ypos = self.xpos(), self.ypos()
        root_item = self.scene.root_ui_node
        parent_edge = self.parentItem()
        parent_node = self.parentItem().parentItem()
        attach_data = {
            "abs_pos": QPointF(xpos, ypos),
            "old_parent": parent_node,
            "top_level_item": self.topLevelItem(),
        }
        # disconnect and remove parent edge
        self.setParentItem(None)
        parent_node.children.remove(self)
        parent_node.edges.remove(parent_edge)
        parent_edge.setParentItem(None)
        self.scene.removeItem(parent_edge)
        # move node to retain correct position
        self.setPos(0, 0)
        move_x = xpos - root_item.xpos() - (self.scene.node_init_pos[0] - root_item.xpos())
        move_y = ypos - root_item.ypos() - (self.scene.node_init_pos[1] - root_item.ypos())
        self.moveBy(move_x, move_y)
        return attach_data

    def attach_to_parent(self, data, parent=None):
        if not parent:
            parent = data['old_parent']
        new_abs_pos = QPointF(self.xpos(), self.ypos())
        # reset parent item
        e = Edge(parent, self)
        e.setParentItem(parent)
        parent.children.append(self)
        parent.edges.append(e)
        parent.sort_children()
        parent_abs_pos = QPointF(parent.xpos(), parent.ypos())
        # reset relative position to parent
        self.setPos(new_abs_pos - parent_abs_pos)

    def collapse_upwards(self):
        """
        Collapses the tree upwards only displaying this node and its children
        :return:
        """
        self.expand_data = self.detach_from_parent()
        # hide parent nodes
        self.expand_data['top_level_item'].hide()

    def expand_upwards(self):
        """
        Expands the tree upwards displaying all expanded parent nodes
        :return:
        """
        self.attach_to_parent(self.expand_data)
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

    def detect_order_change(self):
        """
        Detects if node order has changed and updates model accordingly
        """
        # parent node of self
        parent_node = self.parentItem().parentItem()
        # own child index
        node_index = parent_node.children.index(self)
        # check if node is swapped with left neighbour
        try:
            # can throw IndexError if there is no left neighbour
            left_node = parent_node.children[node_index - 1]
            # check if node is swapped
            if left_node.xpos() > self.xpos():
                # sort children of parent
                sorted_nodes = parent_node.sort_children()
                # change model tree structure accordingly
                self.scene.gui.tree.nodes[parent_node.model_node.id].children = [n.id for n in sorted_nodes]
        except IndexError:
            pass
        # check if node is swapped with right neighbour
        try:
            # can throw IndexError if there is no right neighbour
            right_node = parent_node.children[node_index + 1]
            # check if node is swapped
            if right_node.xpos() < self.xpos():
                # sort children of parent
                sorted_nodes = parent_node.sort_children()
                # change model tree structure accordingly
                self.scene.gui.tree.nodes[parent_node.model_node.id].children = [n.id for n in sorted_nodes]
        except IndexError:
            pass

    def delete_self(self):
        # remove children
        for c in self.children:
            c.delete_self()
        # remove child reference from parent
        parent_node = None
        if self.parentItem():
            parent_node: Node = self.parentItem().parentItem()
            parent_node.children.remove(self)
            parent_node.edges.remove(self.parentItem())
            if not parent_node.children:
                parent_node.bottom_collapse_expand_button.hide()
            self.scene.gui.tree.nodes[parent_node.model_node.id].children.remove(self.model_node.id)
            # remove parent edge and this node
            self.scene.removeItem(self.parentItem())
        else:
            # remove this node
            self.scene.removeItem(self)
        del self.scene.nodes[self.model_node.id]
        if self.scene.gui.tree.root == self.model_node.id:
            self.scene.gui.tree.root = ''
        # remove node from internal tree structure
        del self.scene.gui.tree.nodes[self.model_node.id]
        if parent_node:
            # todo fix display issues
            self.scene.gui.update_tree(parent_node.model_node)
        # remove the property display
        self.scene.parent().remove_property_display()

    def reconnect_edge(self):
        if not self.parentItem():
            Node.logger.error("The edge trying to reconnext does not exist.")
        else:
            self.scene.start_reconnect_edge(self)

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
            # Set correct order for children if node has a parent
            if self.parentItem():
                self.detect_order_change()
            # reposition incoming edge
            if isinstance(self.parentItem(), Edge):
                self.parentItem().change_position()

    def contextMenuEvent(self, menu_event):
        menu = QMenu()
        reconnect_edge_action = QAction("Reconnect Edge")
        parent_exists = True if self.parentItem() else False
        reconnect_edge_action.setEnabled(parent_exists)
        reconnect_edge_action.triggered.connect(self.reconnect_edge)
        menu.addAction(reconnect_edge_action)
        delete_node_action = QAction("Delete Node")
        delete_node_action.setShortcut('Ctrl+D')
        delete_node_action.setToolTip('Delete node and all its children.')
        delete_node_action.triggered.connect(self.delete_self)
        menu.addAction(delete_node_action)
        menu.exec(menu_event.screenPos())
        menu_event.setAccepted(True)


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
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)

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
        self.scene = self.node.scene
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
