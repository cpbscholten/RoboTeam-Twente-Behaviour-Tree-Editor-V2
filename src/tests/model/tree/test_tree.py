import os
from pathlib import Path

import pytest
from controller.utils.file_utils import read_json
from model.exceptions.invalid_tree_json_format_exception import InvalidTreeJsonFormatException
from model.tree.tree import Tree
from model.tree.node import Node


class TestTree(object):
    # valid trees
    tree_dance_strategy = read_json(Path('json/trees/valid/DanceStrategy.json'))
    tree_demo_twente_strategy = read_json(Path('json/trees/valid/DemoTeamTwenteStrategy.json'))
    tree_simple_tree = read_json(Path('json/trees/valid/SimpleTree.json'))

    # invalid trees
    # trees with missing required attributes
    tree_no_data = read_json(Path('json/trees/invalid/DanceStrategyNoData.json'))
    tree_no_name = read_json(Path('json/trees/invalid/DanceStrategyNoName.json'))
    tree_no_nodes = read_json(Path('json/trees/invalid/DanceStrategyNoNodes.json'))
    tree_no_root = read_json(Path('json/trees/invalid/DanceStrategyNoRoot.json'))
    tree_no_title = read_json(Path('json/trees/invalid/DanceStrategyNoTitle.json'))
    tree_no_trees = read_json(Path('json/trees/invalid/DanceStrategyNoTrees.json'))
    # trees with wrong attribute type
    tree_wrong_name_type = read_json(Path('json/trees/invalid/DanceStrategyWrongNameType.json'))
    tree_wrong_root_type = read_json(Path('json/trees/invalid/DanceStrategyWrongRootType.json'))
    tree_wrong_title_type = read_json(Path('json/trees/invalid/DanceStrategyWrongTitleType.json'))
    # trees without nodes or trees
    tree_empty_trees = read_json(Path('json/trees/invalid/DanceStrategyEmptyTrees.json'))
    tree_empty_nodes = read_json(Path('json/trees/invalid/DanceStrategyEmptyNodes.json'))
    # tree file with more than one tree
    tree_too_many_trees = read_json(Path('json/trees/invalid/DanceStrategyTooManyTrees.json'))

    def test_from_json_valid(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert tree.name == 'DanceStrategy'
        assert tree.root == 'tfbqmsn62cc9okkj'
        assert len(tree.nodes) == 3

    def test_from_json_valid2(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert tree.name == 'DemoTeamTwenteStrategy'
        assert tree.root == 'ydjw9of7ndf88'
        assert len(tree.nodes) == 4

    def test_from_json_valid3(self):
        tree = Tree("SimpleTree", "1", {"1": Node("1", "Sequence")})
        assert tree == Tree.from_json(self.tree_simple_tree)

    def test_from_json_invalid_wrong_attribute_types(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_name_type)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_root_type)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_title_type)

    def test_from_json_invalid_missing_attributes(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_data)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_name)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_nodes)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_root)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_title)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_trees)

    def test_from_json_empty_trees_nodes(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_empty_nodes)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_empty_trees)

    def test_from_json_too_many_trees(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_too_many_trees)

    def test_write(self, tmpdir):
        # TODO add case when not valid
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.write(tmpdir, "test.json")
        path = tmpdir / 'test.json'
        read = Tree.from_json(read_json(path))
        assert tree == read

    def test_add_node(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.add_node(Node("1", "title"))
        assert "1"in tree.nodes.keys()

    def test_remove_node(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.remove_node(tree.nodes.get("tfbqmsn62cc9okkj"))
        assert "tfbqmsn62cc9okkj" not in tree.nodes.keys()

    def test_remove_node_not_existent(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.remove_node(Node("non existent node", "title"))
        assert "non existent node" not in tree.nodes.keys()

    def test_remove_node_by_id(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.remove_node_by_id("tfbqmsn62cc9okkj")
        assert "tfbqmsn62cc9okkj" not in tree.nodes.keys()

    def test_remove_node_by_id_not_existent(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.remove_node_by_id("non existent node")
        assert "non existent node" not in tree.nodes.keys()

    def test_create_json1(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert self.tree_dance_strategy == tree.create_json()

    def test_create_json2(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert self.tree_demo_twente_strategy == tree.create_json()

    def test_create_json3(self):
        tree = Tree.from_json(self.tree_simple_tree)
        assert self.tree_simple_tree == tree.create_json()
