from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView

from controller.utils import read_json
from model.tree import Tree, Node as ModelNode
from view.widget.tree_scene import TreeScene
from view.widget.tree_view_toolbar import TreeViewToolbar


class TreeViewWidget(QWidget):

    def __init__(self, parent: QWidget = None):
        """
        The constructor for a tree view widget
        :param parent: The parent widget
        """
        super(TreeViewWidget, self).__init__(parent, Qt.Widget)
        self.layout = QVBoxLayout(self)
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setCursor(Qt.OpenHandCursor)
        self.graphics_view.setRenderHints(QPainter.Antialiasing)
        self.graphics_scene = TreeScene(self.graphics_view, self)
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setMinimumSize(500, 500)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.toolbar = TreeViewToolbar(self.graphics_scene, self)
        self.layout.addWidget(self.graphics_view)
        self.setLayout(self.layout)

    def show_complex_tree(self, view: QGraphicsView):
        """
        Creates a complex example tree and shows it in a scene
        :param view: The Tree view
        :return: The created scene
        """
        nodes = []
        for i in range(40):
            if i % 4 == 0:
                n = ModelNode(str(i), "node node node node node node {}".format(i))
            else:
                n = ModelNode(str(i), "node {}".format(i))
            nodes.append(n)
        nodes[0].add_child(nodes[1].id)
        nodes[0].add_child(nodes[30].id)
        nodes[0].add_child(nodes[31].id)
        nodes[0].add_child(nodes[32].id)
        nodes[0].add_child(nodes[33].id)
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
