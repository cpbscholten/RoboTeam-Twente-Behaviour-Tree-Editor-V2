import time
from random import randint
from threading import Thread

from controller.tree_data import Setup, TreeNode


class HeatmapDemoThread(Thread):

    INTERVAL = 0.25

    session = Setup.get_session()

    def __init__(self, gui):
        super(HeatmapDemoThread, self).__init__()
        self.gui = gui
        self.terminate = False

    def run(self):
        while not self.terminate:
            if self.gui.tree:
                self.init_tree()
                self.change_data()
            time.sleep(self.INTERVAL)

    def stop(self):
        self.terminate = True

    def init_tree(self):
        tree_id = self.gui.tree.name

        node_count = self.session.query(TreeNode).filter_by(tree_id=tree_id).count()
        if node_count != len(self.gui.tree.nodes):
            for node_id in self.gui.tree.nodes:
                db_node = self.session.query(TreeNode).get((node_id, tree_id))
                if not db_node:
                    db_node = TreeNode(id=node_id, tree_id=tree_id, successes=randint(0, 100), runnings=randint(0, 100),
                                       failures=randint(0, 100), waitings=randint(0, 100))
                    self.session.add(db_node)
            self.session.commit()

    def change_data(self):
        tree_id = self.gui.tree.name

        nodes = self.session.query(TreeNode).filter_by(tree_id=tree_id)
        for n in nodes:
            n.successes = max(0, n.successes + randint(-10, 10))
            n.runnings = max(0, n.runnings + randint(-10, 10))
            n.failures = max(0, n.failures + randint(-10, 10))
            n.waitings = max(0, n.waitings + randint(-10, 10))
        self.session.commit()