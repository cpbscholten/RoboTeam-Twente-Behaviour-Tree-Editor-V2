import json
import math
from copy import deepcopy
from typing import List

from PyQt5.QtCore import QRectF, Qt, QPoint, QPointF
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsLineItem

from model.tree import Tree, DisconnectedNode, NodeTypes
from model.tree import Node as ModelNode
from view.elements import Node as ViewNode, CollapseExpandButton


class TreeScene(QGraphicsScene):
    NODE_X_OFFSET = 100
    NODE_Y_OFFSET = 100
    ZOOM_SENSITIVITY = 0.05

    def __init__(self, view, gui, parent=None):
        """
        The constructor for a tree scene
        :param view: The view for this scene
        :param gui: the main window
        :param parent: The parent widget of this scene
        """
        super(TreeScene, self).__init__(QRectF(0, 0, 1, 1), parent)
        self.gui = gui
        self.app = self.gui.app
        self.view = view
        # mapping for model node to view node
        self.nodes = {}
        # disconnected graphical nodes in the view
        self.disconnected_nodes = []
        # Indicates if the scene is in info mode
        self.info_mode = False
        # Indicates if the scene is in simulator mode
        self.simulator_mode = False
        # Indicates if the TreeScene is dragged around
        self.dragging = False
        # The tree ModelNode being added to the scene
        self.adding_node: ModelNode = None
        # The drag drop node being added
        self.drag_drop_node: ViewNode = None
        # The node being connected to the tree
        self.connecting_node = None
        # Line connected to cursor when connecting nodes
        self.connecting_line = None
        # Indicates the node being dragged
        self.dragging_node = None
        # Position data for node reconnection
        self.reconnecting_node = None
        self.reconnect_edge_data = None
        # start position of every node
        self.node_init_pos = None
        # root of the tree
        self.root_ui_node = None

    def add_tree(self, tree: Tree, x: int = None, y: int = 0):
        """
        Adds model tree recursively to the scene
        :param x: The x position for the root node
        :param y: The y position for the root node
        :param tree: Model tree
        """
        # use the top center as default tree position
        if not x:
            x = self.width() / 2
        if not y:
            y = - (self.view.viewport().height() / 2) + ViewNode.NODE_HEIGHT
        self.node_init_pos = (x, y)
        # remove old content
        self.clear()
        tree = deepcopy(tree)
        # check if there is a root, otherwise do not display the tree
        if not tree.root:
            return
        # add disconnected nodes to root
        all_children = [c for node in tree.nodes.values() for c in node.children]
        disconnected_model_nodes = [tree.nodes[node]
                                    for node in tree.nodes if node != tree.root and node not in all_children]
        # sort nodes based on number of children
        disconnected_model_nodes = sorted(disconnected_model_nodes, key=lambda n: len(n.children), reverse=True)
        for i, d_node in enumerate(disconnected_model_nodes):
            d_view_node = DisconnectedNode(d_node)
            tree.nodes[d_view_node.id] = d_view_node
            tree.nodes[tree.root].children.append(d_view_node.id)
        # start recursively drawing tree
        root_node = tree.nodes[tree.root]
        self.root_ui_node = self.add_subtree(tree, root_node)[0]
        self.root_ui_node.top_collapse_expand_button.hide()
        self.addItem(self.root_ui_node)

    def clear(self):
        self.root_ui_node = None
        self.nodes.clear()
        self.disconnected_nodes.clear()
        return super(TreeScene, self).clear()

    def keyReleaseEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            if self.connecting_node:
                self.disconnected_nodes.append(self.connecting_node)
                self.removeItem(self.connecting_line)
                self.app.restoreOverrideCursor()
                # remove reset cursor filter (cursor already reset)
                self.app.removeEventFilter(self.app.wait_for_click_filter)
                node = self.gui.tree.nodes.get(self.connecting_node.id)
                self.connecting_node = None
                self.gui.update_tree(node)
            elif self.reconnecting_node:
                if self.reconnecting_node not in self.disconnected_nodes:
                    self.disconnected_nodes.append(self.reconnecting_node)
                self.removeItem(self.connecting_line)
                self.app.restoreOverrideCursor()
                # remove reset cursor filter (cursor already reset)
                self.app.removeEventFilter(self.app.wait_for_click_filter)
                old_parent = self.gui.tree.nodes[self.reconnect_edge_data['old_parent'].id]
                self.reconnecting_node = None
                self.reconnect_edge_data = None
                self.gui.update_tree(old_parent)

    def add_subtree(self, tree: Tree, subtree_root: ModelNode):
        """
        Recursive functions that adds node and its children to the tree.
        :param tree: The complete tree, used for node lookup
        :param subtree_root: The root of this subtree/branch
        :return: The created subtree root node,
                 the width of both sides of the subtree
        """
        subtree_root_node = ViewNode(*self.node_init_pos, scene=self, title=subtree_root.title,
                                     model_node=subtree_root, node_types=self.gui.load_node_types)
        if isinstance(subtree_root, DisconnectedNode):
            subtree_root_node.top_collapse_expand_button.hide()
        self.nodes[subtree_root.id] = subtree_root_node
        if subtree_root.id not in self.gui.tree.nodes:
            self.gui.tree.nodes[subtree_root.id] = subtree_root
        if subtree_root.id == tree.root:
            connected_children = [c for c in subtree_root.children if not isinstance(tree.nodes[c], DisconnectedNode)]
            middle_index = (len(connected_children) - 1) / 2
        else:
            middle_index = (len(subtree_root.children) - 1) / 2
        # keep track of level width to prevent overlapping nodes
        subtree_left_width = subtree_right_width = 0
        # store the left nodes so that they can be moved left during creation
        left_nodes = []
        # iterate over the left nodes
        for i, child_id in enumerate(subtree_root.children[:math.ceil(middle_index)]):
            child = tree.nodes[child_id]
            # add the child and its own subtree,
            # returned values are used to adjust the nodes position to prevent overlap
            child_view_node, child_subtree_width_left, child_subtree_width_right = self.add_subtree(tree, child)
            subtree_root_node.add_child(child_view_node)
            move_x = - (child_subtree_width_left + child_subtree_width_right)
            # prevent double spacing when there is no middle node
            if i == math.floor(middle_index) and not middle_index.is_integer():
                # use half the offset because the other half is added later for the other part of the tree
                move_x -= self.NODE_X_OFFSET / 2
                child_view_node.moveBy(- (child_subtree_width_right + (self.NODE_X_OFFSET / 2)),
                                       (subtree_root_node.rect().height() / 2) + self.NODE_Y_OFFSET)
            else:
                # use the default node offset
                move_x -= self.NODE_X_OFFSET
                child_view_node.moveBy(- (child_subtree_width_right + self.NODE_X_OFFSET),
                                       (subtree_root_node.rect().height() / 2) + self.NODE_Y_OFFSET)
            # add width to total left subtree width
            subtree_left_width += abs(move_x)
            # move all previous nodes to the left to make room for the new node
            for n in left_nodes:
                n.moveBy(move_x, 0)
            left_nodes.append(child_view_node)
        # add middle node
        if middle_index.is_integer():
            child_id = subtree_root.children[int(middle_index)]
            child = tree.nodes[child_id]
            # add the child and its own subtree,
            # returned values are used to adjust the nodes position to prevent overlap
            child_view_node, child_subtree_width_left, child_subtree_width_right = self.add_subtree(tree, child)
            subtree_root_node.add_child(child_view_node)
            child_view_node.moveBy(0, (subtree_root_node.rect().height() / 2) + self.NODE_Y_OFFSET)
            # move all left nodes further to the left to make room for the middle node
            move_x = - self.NODE_X_OFFSET + child_subtree_width_left
            if child_subtree_width_left > self.NODE_X_OFFSET:
                move_x = - child_subtree_width_left
            for n in left_nodes:
                n.moveBy(move_x, 0)
            subtree_left_width += child_subtree_width_left
            subtree_right_width += child_subtree_width_right
        # iterate over the right nodes
        for i, child_id in enumerate(subtree_root.children[math.floor(middle_index) + 1:]):
            child = tree.nodes[child_id]
            # add the child and its own subtree,
            # returned values are used to adjust the nodes position to prevent overlap
            child_view_node, child_subtree_width_left, child_subtree_width_right = self.add_subtree(tree, child)
            if not isinstance(child, DisconnectedNode):
                subtree_root_node.add_child(child_view_node)
            else:
                self.disconnected_nodes.append(child_view_node)
                self.addItem(child_view_node)
            move_x = subtree_right_width + child_subtree_width_left
            # add width to total right subtree width
            subtree_right_width += child_subtree_width_left + child_subtree_width_right
            # prevent double spacing when there is no middle node
            if i == 0 and not middle_index.is_integer():
                # use half the offset because the other half is added already
                move_x += self.NODE_X_OFFSET / 2
                subtree_right_width += (self.NODE_X_OFFSET / 2)
            else:
                # use the default node offset
                move_x += self.NODE_X_OFFSET
                subtree_right_width += self.NODE_X_OFFSET
            # move node next to the previous node, all the way to the right
            child_view_node.moveBy(move_x, 0)
            if not isinstance(child, DisconnectedNode):
                child_view_node.moveBy(0, (subtree_root_node.rect().height() / 2) + self.NODE_Y_OFFSET)
        # set the widths of both subtree sides to a default value if no children or a smaller child node
        if not subtree_root.children or subtree_left_width < subtree_root_node.rect().width() / 2 or \
                subtree_right_width < subtree_root_node.rect().width() / 2:
            subtree_left_width = subtree_right_width = subtree_root_node.rect().width() / 2
        return subtree_root_node, subtree_left_width, subtree_right_width

    def change_root(self, node_id: str):
        self.gui.tree.root = node_id
        if node_id == '':
            if self.root_ui_node and not self.root_ui_node.parentItem():
                self.disconnected_nodes.append(self.root_ui_node)
            self.root_ui_node = None
        else:
            if self.root_ui_node:
                self.disconnected_nodes.append(self.root_ui_node)
            node = self.nodes[node_id]
            self.root_ui_node = node
            try:
                self.disconnected_nodes.remove(node)
            except ValueError:
                pass
        self.update()
        self.gui.update_tree()

    def update_children(self, node_ids: List[str]):
        for node_id in node_ids:
            if node_id in self.nodes:
                model_node = self.gui.tree.nodes[node_id]
                view_node = self.nodes[node_id]
                if self.view.parent().property_display and \
                        self.view.parent().property_display.node_id in [n.id for n in view_node.nodes_below()]:
                    self.close_property_display()
                for c in view_node.children:
                    c.delete_subtree(update_tree=False)
                for e in view_node.edges:
                    e.setParentItem(None)
                    self.removeItem(e)
                view_node.edges.clear()
                for c_id in model_node.children:
                    child_model_node = self.gui.tree.nodes[c_id]
                    child_view_node = self.add_subtree(self.gui.tree, child_model_node)[0]
                    view_node.add_child(child_view_node)
                self.align_while_colliding()

    def align_tree(self):
        """
        Aligns the tree currently visible in the ui
        """
        if self.gui.tree:
            if self.root_ui_node:
                self.align_from_node(self.root_ui_node)

    def align_while_colliding(self, node: ViewNode = None):
        if not node:
            node = self.root_ui_node
        if self.gui.tree:
            if node:
                colliding_below = [nb for nb in node.nodes_below() if [ci for ci in nb.collidingItems() if isinstance(ci, ViewNode)]]
                colliding_below.sort(key=lambda n: len(n.nodes_below()), reverse=True)
                for node in colliding_below:
                    align_node = node
                    while [ci for ci in node.collidingItems() if isinstance(ci, ViewNode)]:
                        if align_node.parentItem():
                            align_node = align_node.parentItem().parentItem()
                            self.align_from_node(align_node)
                        else:
                            break

    def align_from_node(self, node: ViewNode):
        """
        Align all the children of a node
        Works like add_subtree but repositions existing nodes instead of creating nodes
        :param node: The root of the alignment
        """
        middle_index = (len(node.children) - 1) / 2
        # keep track of level width to prevent overlapping nodes
        subtree_left_width = subtree_right_width = 0
        # store the left nodes so that they can be moved left during repositioning
        left_nodes = []
        # iterate over the left nodes
        for i, child in enumerate(node.children[:math.ceil(middle_index)]):
            # calculate values for position adjustment to prevent overlap
            child_subtree_width_left, child_subtree_width_right = self.align_from_node(child)
            # only align visible nodes
            if node.isVisible() and child.isVisible():
                move_x = - (child_subtree_width_left + child_subtree_width_right)
                # reset node to start position
                child.setPos(0, (node.rect().height() / 2) + self.NODE_Y_OFFSET)
                # prevent double spacing when there is no middle node
                if i == math.floor(middle_index) and not middle_index.is_integer():
                    # use half the offset because the other half is added later for the other part of the tree
                    move_x -= self.NODE_X_OFFSET / 2
                    child.moveBy(- (child_subtree_width_right + (self.NODE_X_OFFSET / 2)), 0)
                else:
                    # use the default node offset
                    move_x -= self.NODE_X_OFFSET
                    child.moveBy(- (child_subtree_width_right + self.NODE_X_OFFSET), 0)
                # add width to total left subtree width
                subtree_left_width += abs(move_x)
                # move all previous nodes to the left to make room for the current node
                for n in left_nodes:
                    n.moveBy(move_x, 0)
                left_nodes.append(child)
        # reposition middle node
        if middle_index.is_integer():
            child = node.children[int(middle_index)]
            # calculate values for position adjustment to prevent overlap
            child_subtree_width_left, child_subtree_width_right = self.align_from_node(child)
            # only align visible nodes
            if node.isVisible() and child.isVisible():
                # reset node to start position
                child.setPos(0, (node.rect().height() / 2) + self.NODE_Y_OFFSET)
                # move all left nodes further to the left to make room for the middle node
                move_x = - self.NODE_X_OFFSET + child_subtree_width_left
                if child_subtree_width_left > self.NODE_X_OFFSET:
                    move_x = - child_subtree_width_left
                for n in left_nodes:
                    n.moveBy(move_x, 0)
                subtree_left_width += child_subtree_width_left
                subtree_right_width += child_subtree_width_right
        # iterate over the right nodes
        right_nodes = node.children[math.floor(middle_index) + 1:]
        if node == self.root_ui_node:
            right_nodes.extend(self.disconnected_nodes)
        for i, child in enumerate(right_nodes):
            # calculate values for position adjustment to prevent overlap
            child_subtree_width_left, child_subtree_width_right = self.align_from_node(child)
            # only align visible nodes
            if node.isVisible() and child.isVisible():
                move_x = subtree_right_width + child_subtree_width_left
                # add width to total right subtree width
                subtree_right_width += child_subtree_width_left + child_subtree_width_right
                # prevent double spacing when there is no middle node
                if i == 0 and not middle_index.is_integer():
                    # use half the offset because the other half is added already
                    move_x += self.NODE_X_OFFSET / 2
                    subtree_right_width += (self.NODE_X_OFFSET / 2)
                else:
                    # use the default node offset
                    move_x += self.NODE_X_OFFSET
                    subtree_right_width += self.NODE_X_OFFSET
                # reset node to start position
                if child not in self.disconnected_nodes:
                    child.setPos(0, (node.rect().height() / 2) + self.NODE_Y_OFFSET)
                else:
                    child.setPos(self.root_ui_node.pos())
                # move node next to the previous node, all the way to the right
                child.moveBy(move_x, 0)
        # set the widths of both subtree sides to a default value if no children or a smaller child node
        if not node.children or subtree_left_width < node.rect().width() / 2 or \
                subtree_right_width < node.rect().width() / 2:
            subtree_left_width = subtree_right_width = node.rect().width() / 2
        return subtree_left_width, subtree_right_width

    def switch_info_mode(self, info_mode: bool):
        self.info_mode = info_mode
        if self.root_ui_node:
            self.root_ui_node.initiate_view(propagate=True)
        for n in self.disconnected_nodes:
            n.initiate_view(propagate=True)

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on the scene
        :param m_event: The mouse press event and its details
        """
        # hide connecting line to prevent it from being clicked
        if self.connecting_line:
            self.connecting_line.hide()
        item = self.itemAt(m_event.scenePos(), self.view.transform())
        if self.connecting_line:
            self.connecting_line.show()
        if self.adding_node:
            x = int(m_event.scenePos().x())
            y = int(m_event.scenePos().y())
            self.start_node_addition(x, y)
            self.adding_node = None
            self.close_property_display()
            return
        elif self.connecting_node:
            if item and (isinstance(item, ViewNode) or (item.parentItem() and isinstance(item.parentItem(), ViewNode))):
                clicked_node = item if isinstance(item, ViewNode) else item.parentItem()
                if clicked_node == self.connecting_node:
                    return
                self.finish_connect_edge(clicked_node)
            elif not item and m_event.button() == Qt.LeftButton:
                self.dragging = True
                self.view.setCursor(Qt.ClosedHandCursor)
            return
        elif self.reconnecting_node:
            if item and (isinstance(item, ViewNode) or (item.parentItem() and isinstance(item.parentItem(), ViewNode))):
                clicked_node = item if isinstance(item, ViewNode) else item.parentItem()
                if clicked_node == self.reconnecting_node:
                    return
                self.finish_reconnect_edge(clicked_node)
            elif not item and m_event.button() == Qt.LeftButton:
                self.dragging = True
                self.view.setCursor(Qt.ClosedHandCursor)
            return
        else:
            if m_event.button() == Qt.LeftButton and item:
                if isinstance(item, CollapseExpandButton):
                    pass
                elif isinstance(item, ViewNode):
                    self.dragging_node = item
                    item.dragging = True
                elif isinstance(item.parentItem(), ViewNode):
                    self.dragging_node = item.parentItem()
                    item.parentItem().dragging = True
                elif item.parentItem():
                    if isinstance(item.parentItem().parentItem(), ViewNode):
                        self.dragging_node = item.parentItem().parentItem()
                        item.parentItem().parentItem().dragging = True
            # Set dragging state of the scene
            elif m_event.button() == Qt.LeftButton:
                self.dragging = True
                self.view.setCursor(Qt.ClosedHandCursor)
            # Remove property display window and save changes
            if not item:
                self.close_property_display()
        super(TreeScene, self).mousePressEvent(m_event)

    def close_property_display(self):
        if self.view.parent().property_display:
            self.view.parent().property_display.setParent(None)
            self.view.parent().property_display.deleteLater()
            self.view.parent().property_display = None

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
        if self.drag_drop_node:
            # initiate connection state if tree has a root
            if self.gui.tree and self.gui.tree.root != '':
                self.connecting_node = self.drag_drop_node
                x, y = self.drag_drop_node.xpos(), self.drag_drop_node.ypos()
                self.connecting_line = QGraphicsLineItem(x, y - self.drag_drop_node.rect().height() / 2, x, y)
                # keep connection line on top
                self.connecting_line.setZValue(1)
                self.addItem(self.connecting_line)
                self.app.add_cross_cursor(self)
            else:
                # add root to model of the tree
                self.gui.tree.root = self.drag_drop_node.id
                self.root_ui_node = self.drag_drop_node
            node = self.gui.tree.nodes.get(self.drag_drop_node.id)
            self.gui.update_tree(node)
            self.drag_drop_node = None
        if self.dragging_node:
            self.dragging_node.mouseMoveEvent(m_event)
            return
        # adjust connection line when connecting node
        if self.connecting_line:
            line = self.connecting_line.line()
            line.setP2(m_event.scenePos() - QPoint(-1, 1))
            self.connecting_line.setLine(line)
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
                if g_item == self.connecting_line:
                    line = self.connecting_line.line()
                    line.setP1(line.p1() + QPointF(dx, dy))
                    self.connecting_line.setLine(line)
                else:
                    g_item.moveBy(dx, dy)

    def zoom(self, zoom_x, zoom_y):
        """
        Zooms the view
        :param zoom_x: Zoom percentage for the x-axis
        :param zoom_y: Zoom percentage for the y-axis
        """
        self.view.scale(zoom_x, zoom_y)

    def wheelEvent(self, wheel_event):
        """
        Handles a mousewheel scroll in the scene
        :param wheel_event: The mousewheel event and its details
        """
        zoom_value = 1 + (self.ZOOM_SENSITIVITY * (wheel_event.delta() / 120))
        self.zoom(zoom_value, zoom_value)

    def dragEnterEvent(self, drag_drop_event):
        if self.drag_drop_node:
            return
        mime_data = drag_drop_event.mimeData()
        if mime_data.hasText() and self.gui.tree:
            drag_drop_event.accept()
            node_type = json.loads(mime_data.text())
            node = NodeTypes.create_node_from_node_type(node_type)
            # setting this attribute starts node addition sequence in the scene
            self.gui.tree.add_node(node)
            node = ViewNode(*self.node_init_pos, scene=self, model_node=node, title=node.title,
                            node_types=self.gui.load_node_types)
            self.drag_drop_node = node
            node.top_collapse_expand_button.hide()
            self.nodes[node.id] = node
            x, y = drag_drop_event.scenePos().x(), drag_drop_event.scenePos().y()
            node.moveBy(x - self.node_init_pos[0], y - self.node_init_pos[1])
            self.addItem(node)
        else:
            drag_drop_event.ignore()

    def dragMoveEvent(self, drag_drop_event):
        x, y = drag_drop_event.scenePos().x(), drag_drop_event.scenePos().y()
        if self.drag_drop_node:
            self.drag_drop_node.setPos(x - self.node_init_pos[0], y - self.node_init_pos[1])

    def dragLeaveEvent(self, drag_drop_event):
        if self.drag_drop_node:
            self.removeItem(self.drag_drop_node)
            self.gui.tree.nodes.pop(self.drag_drop_node.id, None)
            self.drag_drop_node = None

    def start_node_addition(self, x, y):
        """
        Starts node addition sequence, spawn a node and let a connection line follow the cursor
        :param x: Clicked x position in the scene
        :param y: Clicked y position in the scene
        :return:
        """
        # create subtree based on model node
        node = self.add_subtree(self.gui.tree, self.adding_node)[0]
        node.top_collapse_expand_button.hide()
        self.nodes[self.adding_node.id] = node
        # adjust to correct position
        node.moveBy(x - self.node_init_pos[0], y - self.node_init_pos[1])
        self.addItem(node)
        self.gui.tree.add_node(self.adding_node)
        # initiate connection state if tree has a root
        if self.gui.tree and self.gui.tree.root != '':
            self.connecting_node = node
            self.connecting_line = QGraphicsLineItem(x, y - node.rect().height() / 2, x, y)
            # keep connection line on top
            self.connecting_line.setZValue(1)
            self.addItem(self.connecting_line)
        else:
            # add root to model of the tree
            self.gui.tree.root = node.id
            # reset back to normal cursor
            self.app.restoreOverrideCursor()

    def finish_connect_edge(self, parent_node):
        # check for cycles in subtree
        connecting_model_node = self.gui.tree.nodes.get(self.connecting_node.id)
        parent_model_node = self.gui.tree.nodes.get(parent_node.id)
        if TreeScene.check_for_cycles_when_connecting(connecting_model_node,
                                                      parent_model_node, self.gui.tree):
            return
        # remember current node position
        node_pos = (self.connecting_node.xpos(), self.connecting_node.ypos())
        # add child to parent ViewNode
        parent_node.add_child(self.connecting_node)

        # move node back to original position
        self.connecting_node.moveBy(node_pos[0] - self.connecting_node.xpos(),
                                    node_pos[1] - self.connecting_node.ypos())
        # sort the children in the UI and get correct model node order
        sorted_children = parent_node.sort_children()
        # set correct child order
        parent_model_node.children = [c.id for c in sorted_children]
        self.gui.tree.nodes[parent_model_node.id].children = [c.id for c in sorted_children]
        self.removeItem(self.connecting_line)
        # reset back to normal cursor
        self.app.restoreOverrideCursor()
        # remove reset cursor filter (cursor already reset)
        self.app.removeEventFilter(self.app.wait_for_click_filter)
        node = self.gui.tree.nodes.get(self.connecting_node.id)
        self.gui.update_tree(node)
        self.connecting_node = None
        self.connecting_line = None

    def start_reconnect_edge(self, node):
        self.reconnecting_node = node
        self.connecting_line = QGraphicsLineItem(node.xpos(), node.ypos() - node.rect().height() / 2,
                                                 node.xpos(), node.ypos())
        self.connecting_line.setZValue(1)
        self.addItem(self.connecting_line)
        if node.parentItem():
            self.reconnect_edge_data = node.detach_from_parent()
            self.gui.tree.nodes[self.reconnect_edge_data['old_parent'].id].children.remove(node.id)
            node.top_collapse_expand_button.hide()
        self.app.add_cross_cursor(self)

    def finish_reconnect_edge(self, parent_node):
        reconnecting_model_node = self.gui.tree.nodes.get(self.reconnecting_node.id)
        parent_model_node = self.gui.tree.nodes.get(parent_node.id)
        if TreeScene.check_for_cycles_when_connecting(reconnecting_model_node,
                                                      parent_model_node, self.gui.tree):
            return
        self.reconnecting_node.attach_to_parent(self.reconnect_edge_data, parent_node)
        self.reconnecting_node.top_collapse_expand_button.show()
        if self.reconnecting_node in self.disconnected_nodes:
            self.disconnected_nodes.remove(self.reconnecting_node)
        sorted_children = parent_node.sort_children()
        self.gui.tree.nodes[parent_node.id].children = [c.id for c in sorted_children]
        self.removeItem(self.connecting_line)
        # reset back to normal cursor
        self.app.restoreOverrideCursor()
        # remove reset cursor filter (cursor already reset)
        self.app.removeEventFilter(self.app.wait_for_click_filter)
        node = self.gui.tree.nodes.get(self.reconnecting_node.id)
        self.reconnecting_node = None
        self.reconnect_edge_data = None
        self.gui.update_tree(node)

    def change_colors(self, node_colors: dict):
        for node in self.nodes:
            if node in node_colors:
                self.nodes[node].simulator_brush.setColor(node_colors[node])
        self.update()

    @staticmethod
    def check_for_cycles_when_connecting(subtree_node, parent_node: ModelNode, tree: Tree) -> bool:
        cycles = False
        cycles |= True if parent_node.id is subtree_node.id else False
        cycles |= True if parent_node.id in tree.nodes[subtree_node.id].children else False
        for child_id in tree.nodes[subtree_node.id].children:
            cycles |= TreeScene.check_for_cycles_when_connecting(tree.nodes.get(child_id), parent_node, tree)
        return cycles
