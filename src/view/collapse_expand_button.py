from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsObject


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
