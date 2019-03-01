import math
from copy import deepcopy

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem

from model.tree.node import Node as ModelNode
from model.tree.tree import Tree
from src.view.Node import Node as ViewNode
from view.CollapseExpandButton import CollapseExpandButton
from view.Edge import Edge


class TreeScene(QGraphicsScene):

    NODE_X_OFFSET = 50
    NODE_Y_OFFSET = 100
    ZOOM_SENSITIVITY = 0.05

    def __init__(self, view, parent=None):
        """
        The constructor for a tree scene
        :param view: The view for this scene
        :param parent: The parent widget of this scene
        """
        super(TreeScene, self).__init__(QRectF(0, 0, 1, 1), parent)
        self.view = view
        # Indicates if the TreeScene is dragged around
        self.dragging = False
        self.collapsed = False
        # Indicates the node being dragged
        self.dragging_node = None
        self.tree = None
        self.root_ui_node = None

    def add_tree(self, tree: Tree):
        """
        Adds model tree recursively to the scene
        :param tree: Model tree
        """
        # remove old content
        self.clear()
        # store current tree inside scene
        self.tree = tree
        # start recursively drawing tree
        root_node = tree.nodes[tree.root]
        self.root_ui_node = self.add_subtree(tree, root_node, self.width()/2, 0)[0]
        self.addItem(self.root_ui_node)

    def add_subtree(self, tree: Tree, subtree_root: ModelNode, x, y):
        """
        Recursive functions that adds node and its children to the tree.
        :param tree: The complete tree, used for node lookup
        :param subtree_root: The root of this subtree/branch
        :param x: The x position for the root
        :param y: The y position for the root
        :return: The created root UI node,
                 the width of both the left and right part of the subtree and the outermost nodes on both sides
        """
        root_ui_node = ViewNode(x, y, subtree_root.title)
        y += self.NODE_Y_OFFSET
        # keep track of level width to prevent overlapping nodes
        subtree_left_width = subtree_right_width = 0
        middle_index = (len(subtree_root.children) - 1) / 2
        prev_subtree_width_left = prev_subtree_width_right = 0
        prev_x = x
        left_most_node = right_most_node = root_ui_node
        # place the middle child of the root node
        if middle_index.is_integer():
            child_id = subtree_root.children[int(middle_index)]
            child = tree.nodes[child_id]
            # add the child and its own subtree,
            # returned values are used to adjust the nodes position based on the width of the subtree to prevent overlap
            middle_child_ui_node, child_subtree_width_left, child_subtree_width_right, child_left_most, child_right_most = self.add_subtree(tree, child, x, y)
            left_most_node = child_left_most
            right_most_node = child_right_most
            subtree_left_width += child_subtree_width_left
            subtree_right_width += child_subtree_width_right
            prev_subtree_width_left = child_subtree_width_left
            prev_subtree_width_right = child_subtree_width_right
            root_ui_node.add_child(middle_child_ui_node)
        # place the left part of the subtree from inside out
        for i, child_id in enumerate(reversed(subtree_root.children[:math.ceil(middle_index)])):
            child = tree.nodes[child_id]
            # prevent double spacing when there is no middle node
            if i == 0 and not middle_index.is_integer():
                # use half the offset because the other half is added later for the other part of the tree
                child_x = prev_x - (self.NODE_X_OFFSET / 2)
            else:
                child_x = prev_x - (left_most_node.rect().width() / 2) - self.NODE_X_OFFSET
            subtree_left_width += prev_x - child_x
            # add the child and its own subtree,
            # returned values are used to adjust the nodes position based on the subtree width of its neighbour
            child_ui_node, child_subtree_width_left, child_subtree_width_right, child_left_most, child_right_most = self.add_subtree(tree, child, child_x, y)
            left_most_node = child_left_most
            # calculate the offset for the node based on the width of its own subtree and its right neighbours subtree
            move_x = - (child_subtree_width_right + prev_subtree_width_left + (child_right_most.rect().width() / 2))
            child_ui_node.moveBy(move_x, 0)
            # add the offset to the total subtree width
            subtree_left_width += child_subtree_width_left + child_subtree_width_right + (child_right_most.rect().width() / 2)
            prev_x = child_x + move_x
            prev_subtree_width_left = child_subtree_width_left
            root_ui_node.add_child(child_ui_node)
        # reset the last x position to the location of the middle node
        prev_x = x
        # place the right part of the subtree from inside out
        for i, child_id in enumerate(subtree_root.children[math.floor(middle_index) + 1:]):
            child: ModelNode = tree.nodes[child_id]
            # prevent double spacing when there is no middle node
            if i == 0 and not middle_index.is_integer():
                # half the offset because other half is added during the creation of the left part of the subtree
                child_x = prev_x + (self.NODE_X_OFFSET / 2)
            else:
                child_x = prev_x + (right_most_node.rect().width() / 2) + self.NODE_X_OFFSET
            subtree_right_width += child_x - prev_x
            # add the child and its own subtree,
            # returned values are used to adjust the nodes position based on the subtree width of its neighbour
            child_ui_node, child_subtree_width_left, child_subtree_width_right, child_left_most, child_right_most = self.add_subtree(tree, child, child_x, y)
            right_most_node = child_right_most
            # calculate the offset for the node based on the width of its own subtree and its left neighbours subtree
            move_x = child_subtree_width_left + prev_subtree_width_right + (child_left_most.rect().width() / 2)
            child_ui_node.moveBy(move_x, 0)
            # add the offset to the total subtree width
            subtree_right_width += child_subtree_width_left + child_subtree_width_right + (child_left_most.rect().width() / 2)
            prev_x = child_x + move_x
            prev_subtree_width_right = child_subtree_width_right
            root_ui_node.add_child(child_ui_node)
        return root_ui_node, subtree_left_width, subtree_right_width, left_most_node, right_most_node

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on the scene
        :param m_event: The mouse press event and its details
        """
        super(TreeScene, self).mousePressEvent(m_event)
        # If stop function if node is clicked
        item = self.itemAt(m_event.scenePos(), self.view.transform())
        if m_event.button() == Qt.LeftButton and item:
            if isinstance(item, CollapseExpandButton):
                return
            if isinstance(item, ViewNode):
                self.dragging_node = item
                item.dragging = True
            if isinstance(item.parentItem(), ViewNode):
                self.dragging_node = item.parentItem()
                item.parentItem().dragging = True
            return
        # Set dragging state of the scene
        if m_event.button() == Qt.LeftButton:
            self.dragging = True
            self.view.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, m_event):
        """
        Handles a mouse release on the scene
        :param m_event: The mouse release event and its details
        """
        super(TreeScene, self).mouseReleaseEvent(m_event)
        # reset dragging state of the scene and all nodes
        if m_event.button() == Qt.LeftButton:
            if self.dragging:
                self.dragging = False
                self.view.setCursor(Qt.OpenHandCursor)
            elif self.dragging_node:
                # reset node to default mode
                self.dragging_node.dragging = False
                self.dragging_node = None

    def mouseMoveEvent(self, m_event):
        """
        Handles a mouse move on the scene
        :param m_event: The mouse move event and its details
        """
        super(TreeScene, self).mouseMoveEvent(m_event)
        # pass move event to dragged node
        if self.dragging_node:
            self.dragging_node.mouseMoveEvent(m_event)
            return
        # pass mouse move event to top item that accepts hover events
        item = self.itemAt(m_event.scenePos(), self.view.transform())
        if item:
            if item.acceptHoverEvents():
                item.mouseMoveEvent(m_event)
                return
            else:
                # look for parent that accepts hover events
                while item.parentItem():
                    item = item.parentItem()
                    if item.acceptHoverEvents():
                        item.mouseMoveEvent(m_event)
                        return
        # check if scene is being dragged and move all items accordingly
        if self.dragging:
            dx = m_event.scenePos().x() - m_event.lastScenePos().x()
            dy = m_event.scenePos().y() - m_event.lastScenePos().y()
            for g_item in [i for i in self.items() if not i.parentItem()]:
                g_item.moveBy(dx, dy)

    def wheelEvent(self, wheel_event):
        """
        Handles a mousewheel scroll in the scene
        :param wheel_event: The mousewheel event and its details
        """
        scale_by = 1 + (self.ZOOM_SENSITIVITY * (wheel_event.delta() / 120))
        self.view.scale(scale_by, scale_by)
