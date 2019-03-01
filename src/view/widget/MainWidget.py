import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication

from view.widget.TreeViewWidget import TreeViewWidget


class MainWidget(QWidget):

    def __init__(self, parent: QWidget = None):
        """
        Constructor for the main widget
        :param parent: The parent of this widget
        """
        super(MainWidget, self).__init__(parent, Qt.Widget)
        self.setWindowTitle('RoboTeam Behaviour Tree Editor V2')
        self.layout = QVBoxLayout(self)
        self.tree_view_widget = TreeViewWidget()
        self.layout.addWidget(self.tree_view_widget)
        self.setLayout(self.layout)
        self.resize(1000, 800)
