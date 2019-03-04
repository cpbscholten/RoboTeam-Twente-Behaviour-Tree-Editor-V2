from pathlib import Path

from model.config.settings import Settings
from model.tree.collection import Collection
from model.tree.node import Node
from typing import Dict
from controller.utils.file_utils import read_json
from model.tree.tree import Tree


class TestCollection(object):
    path = Path("json/collection/")
    assister_role = Tree.from_json(read_json(Path('json/collection/roles/Assister.json')))
    attack_strategy = Tree.from_json(read_json(Path('json/collection/strategies/AttackStrategy.json')))
    attactic_tactic = Tree.from_json(read_json(Path('json/collection/tactics/Attactic.json')))
    collection: Dict[str, Dict[str, Tree]] = {
        "roles": {"Assister.json": assister_role},
        "strategies": {"AttackStrategy.json": attack_strategy},
        "tactics": {"Attactic.json": attactic_tactic}
    }

    def test_from_path(self):
        collection = Collection.from_path(self.path)
        # collection should not contain the invalid roles/InvalidRole.json
        assert 'InvalidRole' not in collection.collection.get('roles').keys()
        assert Collection(self.collection) == collection

    def test_from_path_default(self):
        def_json = Settings.default_json_folder()
        Settings.alter_default_json_folder(self.path)
        collection = Collection.from_path()
        Settings.alter_default_json_folder(def_json)
        # collection should not contain the invalid roles/InvalidRole.json
        assert 'InvalidRole' not in collection.collection.get('roles').keys()
        assert Collection(self.collection) == collection

    def test_build_collection(self):
        collection = Collection()
        collection.build_collection(self.path)
        # check if hidden file is not added to collection
        assert '.hiddenTree.json' not in collection.collection.get('roles')
        # check if file with wrong file extension is not added
        assert 'TreeWithoutJsonFileExtension' not in collection.collection.get('roles')
        assert Collection(self.collection) == collection

    def test_write_collection(self, tmpdir):
        collection = Collection.from_path(self.path)
        collection.write_collection(tmpdir)
        read = Collection.from_path(tmpdir)
        assert read == collection

    def test_write_collection_default_path(self, tmpdir):
        def_path = Settings.default_json_folder()
        Settings.alter_default_json_folder(tmpdir)
        collection = Collection.from_path()
        collection.write_collection()
        read = Collection.from_path(tmpdir)
        Settings.alter_default_json_folder(def_path)
        assert collection == read

    def test_write_collection_new_file(self, tmpdir):
        collection = Collection.from_path(self.path)
        collection.write_collection(tmpdir)
        collection.add_tree("roles", "tree.json", Tree("name", "1", {"1": Node("1", "node")}))
        collection.write_collection(tmpdir)
        read = Collection.from_path(tmpdir)
        assert read == collection

    def test_write_collection_new_file_new_dir(self, tmpdir):
        collection = Collection({"roles": {"Role.json": Tree("Role", "1", {"1": Node("1", "1")})}})
        collection.write_collection(tmpdir)
        assert collection == Collection.from_path(tmpdir)

    def test_add_tree_folder_exists(self):
        collection = Collection.from_path(self.path)
        tree = Tree("name", "1", {"1": Node("1", "node")})
        collection.add_tree("keeper", "tree.json", tree)
        assert "tree.json" in collection.collection.get('keeper')

    def test_add_tree_folder_not_exists(self):
        collection = Collection.from_path(self.path)
        tree = Tree("name", "1", {"1": Node("1", "node")})
        collection.add_tree("test", "tree.json", tree)
        assert "tree.json" in collection.collection.get('test')

    def test_remove_tree_exists(self):
        collection = Collection.from_path(self.path)
        assert "Assister.json" in collection.collection.get('roles')
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_not_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection.get('roles')
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_by_name_exists(self):
        collection = Collection.from_path(self.path)
        assert "Assister.json" in collection.collection.get('roles')
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_by_name_not_exists(self):
        collection = Collection.from_path(self.path)
        # add a tree, so the if statement goes to the else
        collection.add_tree("roles", "test", Tree('roles', '1'))
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_by_name_dir_not_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree_by_name("test", "Assister")
        assert "test" not in collection.collection.keys()

    def test_remove_tree_by_name_tree_not_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')
