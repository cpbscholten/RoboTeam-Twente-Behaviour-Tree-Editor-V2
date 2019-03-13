import pytest
from pathlib import Path
from typing import Dict

from controller.utils.file_utils import read_json
from model.exceptions.cycle_in_tree_exception import CycleInTreeException
from model.exceptions.incorrect_tree_structure_exception import IncorrectTreeStructureException
from model.exceptions.unconnected_node_exception import UnconnectedNodeException
from model.tree.collection import Collection
from model.tree.tree import Tree

class TestVerification(object):

    path = Path("json/collection/")
    assister_role = Tree.from_json(read_json(Path('json/collection/roles/Assister.json')))
    attack_strategy = Tree.from_json(read_json(Path('json/collection/strategies/AttackStrategy.json')))
    attactic_tactic = Tree.from_json(read_json(Path('json/collection/tactics/Attactic.json')))

    # invalid trees
    simple_cyclic_tree = Tree.from_json(read_json(Path('json/verification/SimpleCyclicTree.json')))
    simple_unconnected_tree = Tree.from_json(read_json(Path('json/verification/SimpleTreeWithUnconnectedNodes.json')))
    simple_invalid_composites_tree = Tree.from_json(read_json(Path('json/verification/InvalidCompositesTree.json')))
    simple_invalid_decorator_tree = Tree.from_json(read_json(Path('json/verification/InvalidDecoratorTree.json')))

    # valid trees
    simple_non_cyclic_tree = Tree.from_json(read_json(Path('json/verification/SimpleNonCyclicTree.json')))
    complex_tree = Tree.from_json(read_json(Path('json/verification/SimpleDefendTactic.json')))
    offensive_strategy_tree = Tree.from_json(read_json(Path('json/verification/OffensiveStrategy.json')))

    collection: Dict[str, Dict[str, Tree]] = {
        "roles": {"Assister.json": assister_role, "InvalidCompositesTree.json": simple_invalid_composites_tree},
        "strategies": {"AttackStrategy.json": attack_strategy, "OffensiveStrategy.json": offensive_strategy_tree},
        "tactics": {"Attactic.json": attactic_tactic, "SimpleDefendTactic.json": complex_tree}
    }

    def test_simple_tree_with_cycle(self):
        collection = Collection(self.collection)
        tree = self.simple_cyclic_tree
        assert not collection.verify_tree(tree)

    def test_simple_valid_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_non_cyclic_tree
        assert collection.verify_tree(tree)

    def test_simple_unconnected_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_unconnected_tree
        assert not collection.verify_tree(tree)

    def test_invalid_composites_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_invalid_composites_tree
        assert not collection.verify_tree(tree, "roles")

    def test_invalid_decorator_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_invalid_decorator_tree
        assert not collection.verify_tree(tree, "roles")

    def test_complex_tree(self):
        collection = Collection(self.collection)
        tree = self.complex_tree
        result = collection.get_category_from_node(tree.root)
        assert "tactics" == result
        assert collection.verify_tree(tree, "tactics")

    def test_offensive_strategy(self):
        collection = Collection(self.collection)
        tree = self.offensive_strategy_tree
        # assert collection.get_category_from_node("sx6fvrxlaoudhmmq9") == "roles"
        assert collection.verify_tree(tree, "strategies")



