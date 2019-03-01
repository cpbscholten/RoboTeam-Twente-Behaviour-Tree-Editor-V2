from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsPixmapItem


class CollapseExpandButton(QGraphicsPixmapItem):

    def __init__(self, parent):
        """
        The constructor of a collapse/expand button
        :param parent: The parent node where the button belongs to
        """
        self.node = parent
        # TODO: Use a global resource directory
        self.expand_icon = QPixmap("view/icon/expand.png")
        self.collapse_icon = QPixmap("view/icon/collapse.png")
        super(CollapseExpandButton, self).__init__(self.collapse_icon)
        self.setCursor(Qt.PointingHandCursor)
        self.isCollapsed = False

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on the button: Change button icon and expand/collapse the node's children
        :param m_event: The mouse press event and its details
        """
        if self.isCollapsed:
            self.node.expand()
            self.isCollapsed = False
            self.setPixmap(self.collapse_icon)
        else:
            self.node.collapse()
            self.isCollapsed = True
            self.setPixmap(self.expand_icon)
