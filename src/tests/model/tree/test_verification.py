import pytest
from controller.utils.file_utils import read_json
from model.exceptions.cycle_in_tree_exception import CycleInTreeException
from model.exceptions.unconnected_node_exception import UnconnectedNodeException
from model.tree.tree import Tree
from model.tree.verification import Verification


class TestVerification(object):
    # invalid trees
    simple_cyclic_tree = read_json('json/verification/SimpleCyclicTree.json')
    simple_unconnected_tree = read_json('json/verification/SimpleTreeWithUnconnectedNodes.json')

    # valid trees
    simple_non_cyclic_tree = read_json('json/verification/SimpleNonCyclicTree.json')
    complex_tree = read_json('json/verification/SimpleDefendTactic.json')

    def test_simple_tree_with_cycle(self):
        tree = Tree.from_json(self.simple_cyclic_tree)
        with pytest.raises(CycleInTreeException):
            Verification.verify_tree(tree)

    def test_simple_valid_tree(self):
        tree = Tree.from_json(self.simple_non_cyclic_tree)
        assert Verification.verify_tree(tree)

    def test_simple_unconnected_tree(self):
        tree = Tree.from_json(self.simple_unconnected_tree)
        with pytest.raises(UnconnectedNodeException):
            Verification.verify_tree(tree)

    def test_complex_tree(self):
        tree = Tree.from_json(self.complex_tree)
        assert Verification.verify_tree(tree)




