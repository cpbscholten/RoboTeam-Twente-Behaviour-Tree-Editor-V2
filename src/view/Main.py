import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QApplication

from controller.utils.json_utils import read_json
from model.tree.node import Node as ModelNode
from model.tree.tree import Tree
from src.view.TreeScene import TreeScene


class MainWidget(QWidget):

    def __init__(self, parent: QWidget = None):
        """
        Constructor for the main widget
        :param parent: The parent of this widget
        """
        super(MainWidget, self).__init__(parent, Qt.Widget)
        self.setWindowTitle('RoboTeam Behaviour Tree Editor V2')
        self.layout = QVBoxLayout(self)
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setCursor(Qt.OpenHandCursor)
        self.graphics_view.setRenderHints(QPainter.Antialiasing)
        self.graphics_scene = self.show_complex_tree(self.graphics_view)
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setMinimumSize(500, 500)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.graphics_view, 100)
        self.setLayout(self.layout)
        self.resize(1000, 800)

    def show_complex_tree(self, view: QGraphicsView):
        """
        Creates a complex example tree and shows it in a scene
        :param view: The Tree view
        :return: The created scene
        """
        nodes = []
        for i in range(30):
            if i % 4 == 0:
                n = ModelNode(str(i), "node node node node node node {}".format(i))
            else:
                n = ModelNode(str(i), "node {}".format(i))
            nodes.append(n)
        nodes[0].add_child(nodes[1].id)
        nodes[0].add_child(nodes[25].id)
        nodes[0].add_child(nodes[2].id)
        nodes[1].add_child(nodes[3].id)
        nodes[1].add_child(nodes[14].id)
        nodes[1].add_child(nodes[4].id)
        nodes[1].add_child(nodes[15].id)
        nodes[2].add_child(nodes[5].id)
        nodes[2].add_child(nodes[16].id)
        nodes[2].add_child(nodes[17].id)
        nodes[2].add_child(nodes[18].id)
        nodes[2].add_child(nodes[19].id)
        nodes[4].add_child(nodes[9].id)
        nodes[4].add_child(nodes[10].id)
        nodes[4].add_child(nodes[15].id)
        nodes[4].add_child(nodes[11].id)
        nodes[5].add_child(nodes[12].id)
        nodes[5].add_child(nodes[13].id)
        nodes[15].add_child(nodes[20].id)
        nodes[15].add_child(nodes[21].id)
        nodes[15].add_child(nodes[22].id)
        nodes[14].add_child(nodes[23].id)
        nodes[25].add_child(nodes[26].id)
        nodes[25].add_child(nodes[27].id)
        nodes[25].add_child(nodes[28].id)
        nodes[25].add_child(nodes[29].id)
        tree = Tree("Tree 0", nodes[0].id, {n.id: n for n in nodes})
        scene = TreeScene(view, self)
        scene.add_tree(tree)
        return scene

    def show_example_json_tree(self, view: QGraphicsView):
        """
        Shows an example tree from a json file
        :param view: The Tree view
        :return: The created scene
        TODO: Proper interaction with the controller
        """
        tree_json = read_json("SimpleDefendTactic.json")
        tree = Tree.from_json(tree_json)
        scene = TreeScene(view, self)
        scene.add_tree(tree)
        return scene


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_widget = MainWidget()
    main_widget.show()
    exit_state = app.exec()
    sys.exit(exit_state)

