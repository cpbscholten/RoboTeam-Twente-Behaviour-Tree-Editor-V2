import pytest

from model.config.node_types import NodeTypes
from model.config.settings import Settings
from model.exceptions.invalid_node_type_exception import InvalidNodeTypeException
from model.tree.node import Node


class TestNodeTypes:
    def test_from_csv(self):
        node_types = NodeTypes.from_csv(Settings.default_node_types_folder())
        assert '.hiddenfile.csv' not in node_types.node_types.keys()
        assert 'filewithotherextension.abc' not in node_types.node_types.keys()
        assert 'composites' in node_types.node_types.keys()
        assert 'conditions' in node_types.node_types.keys()
        assert 'decorators' in node_types.node_types.keys()
        assert 'other' in node_types.node_types.keys()
        assert 'skills' in node_types.node_types.keys()

    def test_from_csv_custom_path(self, tmpdir):
        node_types = NodeTypes.from_csv()
        node_types.write(tmpdir)
        node_types_custom = NodeTypes.from_csv(tmpdir)
        assert node_types == node_types_custom

    def test_write_default_path(self, tmpdir):
        # case where path is not set and not called
        node_types = NodeTypes.from_csv()
        def_path = Settings.default_node_types_folder()
        Settings.alter_default_node_types_folder(tmpdir)
        # test if writing does not return in an error
        node_types.write()
        read = NodeTypes.from_csv(tmpdir)
        Settings.alter_default_node_types_folder(def_path)
        assert node_types == read

    def test_write_default_path2(self, tmpdir):
        # case where the path has been set, but not called in self.write()
        node_types = NodeTypes.from_csv()
        node_types.path = tmpdir
        # test if writing does not return in an error
        node_types.write()
        read = NodeTypes.from_csv(tmpdir)
        assert node_types == read

    # noinspection PyTypeChecker
    def test_node_type_validity(self):
        with pytest.raises(InvalidNodeTypeException):
            NodeTypes.check_node_type_validity([])
        with pytest.raises(InvalidNodeTypeException):
            NodeTypes.check_node_type_validity([True])
        assert True is NodeTypes.check_node_type_validity(['a'])

    def test_create_node_from_type_exists(self):
        node_from_node_type = NodeTypes.create_node_from_node_type(["Sequence", "a", "b"])
        assert "Sequence" == node_from_node_type.title
        assert "a" in node_from_node_type.attributes.get("properties").keys()
        assert "b" in node_from_node_type.attributes.get("properties").keys()

    def test_add_node_type(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # change the path, so the original config file does not get overridden
        node_types.path = tmpdir
        # check if a new category gets created if it does not exist
        node_types.add_node_type("test", "test_node")
        assert 'test'in node_types.node_types.keys()
        assert 'test_node' in node_types.node_types.get('test')[0]
        # check a node type with attributes
        node_types.add_node_type("test1", "test_node1", ["a"])
        assert 'test_node1' in node_types.node_types.get("test1")[0]
        assert 2 == len(node_types.node_types.get('test1')[0])
        # add one to an existing category
        node_types.add_node_type('test', 'test_node2')
        assert 2 == len(node_types.node_types.get('test'))

    def test_remove_node_type(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # change the path, so the original config file does not get overridden
        node_types.path = tmpdir
        node_types.add_node_type("test", "test")
        node_types.remove_node_type("test", ["test"])
        assert 0 == len(node_types.node_types.get('test'))
        # remove a nde from a category that does not exist
        node_types.remove_node_type("abcdefg", ["sequence"])
        assert "abcdefg" not in node_types.node_types.keys()
        # remove a node that does not exist
        node_types.add_category("abcdefg")
        assert 0 == len(node_types.node_types.get("abcdefg"))
        node_types.remove_node_type("abcdefg", ["sequence"])
        assert 0 == len(node_types.node_types.get("abcdefg"))

    def test_update_node_type(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # change the path, so the original config file does not get overridden
        node_types.path = tmpdir
        # update a node type where the category does not exist
        node_types.update_node_type("test", "test", ['test', "a"])
        assert 'test' not in node_types.node_types.keys()
        # update a node type that does not exist
        node_types.add_category('test')
        node_types.update_node_type("test", "test", ['test', "a"])
        assert 'test' in node_types.node_types.keys()
        assert 0 == len(node_types.node_types.get('test'))
        # update a node type that exists
        node_types.add_node_type('test', 'test')
        node_types.update_node_type("test", ["test"], ['test', "a"])
        assert 'test' in node_types.node_types.keys()
        assert 1 == len(node_types.node_types.get('test'))
        assert ["test", "a"] == node_types.node_types.get('test')[0]

    def test_add_category(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # change the path, so the original config file does not get overridden
        node_types.path = tmpdir
        # add a new category that already exists
        assert 'conditions' in node_types.node_types.keys()
        conditions = node_types.node_types.get('conditions')
        node_types.add_category('conditions')
        assert 'conditions' in node_types.node_types
        assert conditions == node_types.node_types.get('conditions')
        # test creating a new category
        assert 'test' not in node_types.node_types
        node_types.add_category("test")
        assert 'test' in node_types.node_types

    def test_remove_category(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # change the path, so the original config file does not get overridden
        node_types.path = tmpdir
        # test removing existing category
        assert 'conditions' in node_types.node_types
        node_types.remove_category("conditions")
        assert 'conditions' not in node_types.node_types
        # test removing a non existing node_type category
        assert 'test' not in node_types.node_types
        node_types.remove_category("conditions")
        assert 'test' not in node_types.node_types

    def test_get_node_type_by_name(self):
        node_types = NodeTypes.from_csv()
        # assert that the node_type test does not exist
        for category, types in node_types.node_types.items():
            for node_type in types:
                assert node_type[0] != "test"
        assert [] == node_types.get_node_type_by_name('test')
        # check for a existing node
        assert [('composites', ["Sequence"])] == node_types.get_node_type_by_name('Sequence')
        assert [('conditions', ["HasBall"]), ("conditions", ["HasBall"])] == node_types.get_node_type_by_name("HasBall")

    def test_get_node_type_by_node(self):
        node_types = NodeTypes.from_csv()
        # assert that the node_type test does not exist
        for category, types in node_types.node_types.items():
            for node_type in types:
                assert node_type[0] != "test"
        assert [] == node_types.get_node_type_by_node(Node("a", "test"))
        # check for a existing node
        assert [('composites', ["Sequence"])] == node_types.get_node_type_by_node(Node('a', 'Sequence'))
