import random

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QFontMetrics
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem, QWidget

from src.view.Edge import Edge


class Node(QGraphicsEllipseItem):
    i = 0
    NODE_MIN_WIDTH = 100
    NODE_MAX_WIDTH = 150
    NODE_HEIGHT = 50

    def __init__(self, x: float, y: float, title: str = None, parent: QWidget = None):
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
        Node.i += 1
        # add node name label centered in the eclipse, elide if title is too long
        self.node_text = QGraphicsSimpleTextItem()
        metrics = QFontMetrics(self.node_text.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, self.NODE_MAX_WIDTH)
        self.node_text.setText(elided_title)
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
        # give node a random color
        # TODO: Determine color scheme for nodes
        self.setBrush(QBrush(QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

    def add_child(self, child):
        """
        Add a child node
        Inheritance looks like: parent > edge > child
        :param child: Another ui node
        """
        edge = Edge(self, child)
        edge.setParentItem(self)

    def xoffset(self):
        """
        recursively adds the relative x distances from this node up until the root node.
        :return: the sum of the relative x distances
        """
        if self.parentItem():
            return self.pos().x() + self.parentItem().xoffset()
        else:
            return self.pos().x()

    def yoffset(self):
        """
        recursively adds the relative y distances from this node up until the root node.
        :return: the sum of the relative y distances
        """
        if self.parentItem():
            return self.pos().y() + self.parentItem().yoffset()
        else:
            return self.pos().y()

    def xpos(self):
        """
        Calculates the x position of this node using the x offset
        :return: the x position of the node
        """
        return self.rect().x() + self.rect().width() / 2 + self.xoffset()

    def ypos(self):
        """
        Calculates the y position of this node using the y offset
        :return: the y position of the node
        """
        return self.rect().y() + self.rect().height() / 2 + self.yoffset()

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on a node
        :param m_event: The mouse press event and its details
        """
        super(Node, self).mousePressEvent(m_event)
        if m_event.button() == Qt.RightButton:
            # change color
            self.setBrush(QBrush(QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

    def mouseReleaseEvent(self, m_event):
        """
        Handles a mouse release on a node
        :param m_event: The mouse release event and its details
        """
        super(Node, self).mouseReleaseEvent(m_event)
        # reset node to default mode
        self.dragging = False
        self.scene().dragging_node = None

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

