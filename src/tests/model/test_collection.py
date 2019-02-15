from model.exceptions.TreeNotFoundException import TreeNotFoundException
from model.tree.collection import Collection
from model.tree.node import Node
from model.tree.tree import Tree
from typing import Dict
from controller.utils.json_utils import read_json, write_json
import pytest

class TestCollection(object):
    path = "json/collection/"
    assister_role = Tree.from_json(read_json('json/collection/roles/Assister.json'))
    attack_strategy = Tree.from_json(read_json('json/collection/strategies/AttackStrategy.json'))
    attactic_tactic = Tree.from_json(read_json('json/collection/tactics/Attactic.json'))
    collection: Dict[str, Dict[str, Tree]] = {
        "roles": {"Assister.json": assister_role},
        "strategies": {"AttackStrategy.json": attack_strategy},
        "tactics": {"Attactic.json": attactic_tactic}
    }

    def test_from_path(self):
        collection = Collection.from_path(self.path)
        # collection should not contain the invalid roles/InvalidRole.json
        assert 'InvalidRole' not in collection.collection['roles'].keys()
        assert Collection(self.collection) == collection

    def test_build_collection(self):
        collection = Collection()
        collection.build_collection(self.path)
        assert Collection(self.collection) == collection
        # check if hidden file is not added to collection
        assert '.hiddenTree' not in collection.collection['roles']
        # check if file with wrong file extension is not added
        assert 'TreeWithoutJsonFileExtension' not in collection.collection['roles']

    def test_write_collection(self, tmpdir):
        collection = Collection.from_path(self.path)
        collection.write_collection(str(tmpdir) + "/")
        read = Collection.from_path(str(tmpdir) + "/")
        assert read == collection

    def test_write_collection_new_file(self, tmpdir):
        collection = Collection.from_path(self.path)
        collection.write_collection(str(tmpdir) + "/")
        collection.add_tree("roles", "tree.json", Tree("name", "1", {"1": Node("1", "node")}))
        collection.write_collection(str(tmpdir) + '/')
        read = Collection.from_path(str(tmpdir) + "/")
        assert read == collection

    def test_write_collection_new_file_new_dir(self, tmpdir):
        collection = Collection({"roles": {"Role.json": Tree("Role", "1", {"1": Node("1", "1")})}})
        collection.write_collection(str(tmpdir) + "/")
        assert collection == Collection.from_path(str(tmpdir) + "/")

    def test_add_tree_folder_exists(self):
        collection = Collection.from_path(self.path)
        tree = Tree("name", "1", {"1": Node("1", "node")})
        collection.add_tree("keeper", "tree.json", tree)
        assert "tree.json" in collection.collection['keeper']

    def test_add_tree_folder_not_exists(self):
        collection = Collection.from_path(self.path)
        tree = Tree("name", "1", {"1": Node("1", "node")})
        collection.add_tree("test", "tree.json", tree)
        assert "tree.json" in collection.collection['test']

    def test_remove_tree_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection['roles']

    def test_remove_tree_not_exists(self):
        collection = Collection.from_path(self.path)
        with pytest.raises(TreeNotFoundException):
            collection.remove_tree("strategies", "Assister.json")

    def test_remove_tree_by_name_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree_by_name('roles', "Assister")
        print(collection.collection['roles'])
        assert "Assister.json" not in collection.collection['roles']

    def test_remove_tree_by_name_dir_not_exists(self):
        collection = Collection.from_path(self.path)
        with pytest.raises(TreeNotFoundException):
            collection.remove_tree_by_name("test", "Assister")

    def test_remove_tree_by_name_tree_not_exists(self):
        collection = Collection.from_path(self.path)
        with pytest.raises(TreeNotFoundException):
            collection.remove_tree_by_name("roles", "test")
