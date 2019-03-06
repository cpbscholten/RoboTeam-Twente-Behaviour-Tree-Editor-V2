from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton

from view.widget.tree_scene import TreeScene


class TreeViewToolbar(QWidget):

    def __init__(self, scene: TreeScene, parent=None):
        """
        The constructor for a tree view toolbar
        :param scene: The tree scene for this toolbar
        :param parent: The parent widget
        """
        super(TreeViewToolbar, self).__init__(parent, Qt.Widget)
        self.scene = scene
        self.layout = QVBoxLayout(self)
        self.zoom_in_button = ToolbarButton(QIcon("view/icon/zoom_in.svg"))
        self.zoom_in_button.clicked.connect(lambda: self.scene.zoom(1.25, 1.25))
        self.zoom_out_button = ToolbarButton(QIcon("view/icon/zoom_out.svg"))
        self.zoom_out_button.clicked.connect(lambda: self.scene.zoom(0.75, 0.75))
        self.filter_button = ToolbarButton(QIcon("view/icon/filter.svg"))
        # TODO filter implementation
        self.reset_button = ToolbarButton(QIcon("view/icon/reset.svg"))
        self.reset_button.clicked.connect(self.scene.align_tree)
        self.layout.addWidget(self.zoom_in_button)
        self.layout.addWidget(self.zoom_out_button)
        self.layout.addWidget(self.filter_button)
        self.layout.addWidget(self.reset_button)
        self.setLayout(self.layout)
        self.setGeometry(10, 10, self.layout.sizeHint().width(), self.layout.sizeHint().height())


class ToolbarButton(QPushButton):

    def __init__(self, icon: QIcon):
        """
        The constructor for a toolbar button
        :param icon: The icon for this button
        """
        super(ToolbarButton, self).__init__(icon, "")
        self.setFixedSize(30, 30)
