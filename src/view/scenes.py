import math

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsLineItem

from model.tree import Tree
from model.tree import Node as ModelNode
from view.elements import Node as ViewNode, CollapseExpandButton


class TreeScene(QGraphicsScene):

    NODE_X_OFFSET = 50
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
        # Indicates if the TreeScene is dragged around
        self.dragging = False
        # The tree ModelNode being added to the scene
        self.adding_node: ModelNode = None
        # The node being connected to the tree
        self.connecting_node = None
        # Line connected to cursor when connecting nodes
        self.connecting_line = None
        # Indicates the node being dragged
        self.dragging_node = None
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
        # check if there is a root, otherwise do not display the tree
        if tree.root == '':
            return
        # start recursively drawing tree
        root_node = tree.nodes[tree.root]
        self.root_ui_node = self.add_subtree(tree, root_node)[0]
        self.root_ui_node.top_collapse_expand_button.hide()
        self.addItem(self.root_ui_node)

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
                child_view_node.moveBy(- (child_subtree_width_right + (self.NODE_X_OFFSET / 2)), self.NODE_Y_OFFSET)
            else:
                # use the default node offset
                move_x -= self.NODE_X_OFFSET
                child_view_node.moveBy(- (child_subtree_width_right + self.NODE_X_OFFSET), self.NODE_Y_OFFSET)
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
            child_view_node.moveBy(0, self.NODE_Y_OFFSET)
            # move all left nodes further to the left to make room for the middle node
            move_x = - self.NODE_X_OFFSET
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
            subtree_root_node.add_child(child_view_node)
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
            child_view_node.moveBy(move_x, self.NODE_Y_OFFSET)
        # set the widths of both subtree sides to a default value if no children or a smaller child node
        if not subtree_root.children or subtree_left_width < subtree_root_node.rect().width() / 2 or \
                subtree_right_width < subtree_root_node.rect().width() / 2:
            subtree_left_width = subtree_right_width = subtree_root_node.rect().width() / 2
        return subtree_root_node, subtree_left_width, subtree_right_width

    def align_tree(self):
        """
        Aligns the tree currently visible in the ui
        """
        if self.gui.tree and self.root_ui_node:
            self.align_from_node(self.root_ui_node)

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
                child.setPos(0, self.NODE_Y_OFFSET)
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
                child.setPos(0, self.NODE_Y_OFFSET)
                # move all left nodes further to the left to make room for the middle node
                move_x = - self.NODE_X_OFFSET
                if child_subtree_width_left > self.NODE_X_OFFSET:
                    move_x = - child_subtree_width_left
                for n in left_nodes:
                    n.moveBy(move_x, 0)
                subtree_left_width += child_subtree_width_left
                subtree_right_width += child_subtree_width_right
        # iterate over the right nodes
        for i, child in enumerate(node.children[math.floor(middle_index) + 1:]):
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
                child.setPos(0, self.NODE_Y_OFFSET)
                # move node next to the previous node, all the way to the right
                child.moveBy(move_x, 0)
        # set the widths of both subtree sides to a default value if no children or a smaller child node
        if not node.children or subtree_left_width < node.rect().width() / 2 or \
                subtree_right_width < node.rect().width() / 2:
            subtree_left_width = subtree_right_width = node.rect().width() / 2
        return subtree_left_width, subtree_right_width

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on the scene
        :param m_event: The mouse press event and its details
        """
        super(TreeScene, self).mousePressEvent(m_event)
        item = self.itemAt(m_event.scenePos(), self.view.transform())
        if self.adding_node:
            x = int(m_event.scenePos().x())
            y = int(m_event.scenePos().y())
            self.start_node_addition(x, y)
            self.adding_node = None
        elif self.connecting_node:
            if isinstance(item, ViewNode) or isinstance(item.parentItem(), ViewNode):
                clicked_node = item if isinstance(item, ViewNode) else item.parentItem()
                self.finish_node_addition(clicked_node)
                self.connecting_node = None
                self.connecting_line = None
        else:
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
            # Remove property display window and save changes
            if self.view.parent().property_display is not None:
                self.view.parent().property_display.update_properties()
                self.view.parent().property_display.setParent(None)
                self.view.parent().property_display.deleteLater()
                self.view.parent().property_display = None
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
        # adjust connection line when connecting node
        if self.connecting_node:
            line = self.connecting_line.line()
            line.setP2(m_event.scenePos())
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

    def start_node_addition(self, x, y):
        """
        Starts node addition sequence, spawn a node and let a connection line follow the cursor
        :param x: Clicked x position in the scene
        :param y: Clicked y position in the scene
        :return:
        """
        # create node based on model node
        node = ViewNode(*self.node_init_pos, scene=self, model_node=self.adding_node, title=self.adding_node.title,
                        node_types=self.gui.load_node_types)
        # adjust to correct position
        node.moveBy(x - self.node_init_pos[0], y - self.node_init_pos[1])
        self.addItem(node)
        # initiate connection state if tree has a root
        if self.gui.tree and self.gui.tree.root != '':
            self.connecting_node = node
            self.connecting_line = QGraphicsLineItem(x, y - node.rect().height() / 2, x, y)
            # keep connection line on top
            self.connecting_line.setZValue(-1)
            self.addItem(self.connecting_line)
        else:
            # top root node can not collapse upwards
            node.top_collapse_expand_button.hide()
            # add root to model of the tree
            self.gui.tree.add_node(node.model_node)
            self.gui.tree.root = node.model_node.id
            # reset back to normal cursor
            self.app.restoreOverrideCursor()

    def finish_node_addition(self, parent_node):
        # remember current node position
        node_pos = (self.connecting_node.xpos(), self.connecting_node.ypos())
        # add child to parent ViewNode
        parent_node.add_child(self.connecting_node)
        # move node back to original position
        self.connecting_node.moveBy(node_pos[0] - self.connecting_node.xpos(),
                                    node_pos[1] - self.connecting_node.ypos())
        # add node to model of the tree
        self.gui.tree.add_node(self.connecting_node.model_node)
        # sort the children in the UI and get correct model node order
        sorted_children = parent_node.sort_children()
        # set correct child order
        parent_node.model_node.children = [c.id for c in sorted_children]
        self.removeItem(self.connecting_line)
        # reset back to normal cursor
        self.app.restoreOverrideCursor()
        # remove reset cursor filter (cursor already reset)
        self.app.removeEventFilter(self.app.wait_for_click_filter)
