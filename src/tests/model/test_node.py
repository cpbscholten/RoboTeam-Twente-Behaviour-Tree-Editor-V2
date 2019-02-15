import pytest

from model.exceptions.AttributeNotFoundException import AttributeNotFoundException
from model.exceptions.ChildNotFoundException import ChildNotFoundException
from model.exceptions.InvalidTreeException import InvalidTreeException
from model.tree.node import Node
from controller.utils.json_utils import read_json


class TestNode(object):
    # valid node files and objects
    node_attributes_children = Node("1", "node", {"a": True}, ["2", "3"])
    node_attributes_children_json = read_json('json/nodes/valid/NodeAttributesChildren.json')
    node_children_no_attributes = Node("1", "node", {}, ["2", "3"])
    node_children_no_attributes_json = read_json('json/nodes/valid/NodeChildrenNoAttributes.json')
    node_attributes_no_children = Node("1", "node", {"a": True})
    node_attributes_no_children_json = read_json('json/nodes/valid/NodeAttributesNoChildren.json')
    node_no_attributes_children = Node("1", "node")
    node_no_attributes_children_json = read_json('json/nodes/valid/NodeNoAttributesChildren.json')

    # invalid node files
    node_no_id = read_json('json/nodes/invalid/NodeNoId.json')
    node_no_title = read_json('json/nodes/invalid/NodeNoTitle.json')
    node_wrong_children_type = read_json('json/nodes/invalid/NodeWrongChildrenType.json')
    node_wrong_id_type = read_json('json/nodes/invalid/NodeWrongIdType.json')
    node_wrong_title_type = read_json('json/nodes/invalid/NodeWrongTitleType.json')

    def test_from_json(self):
        assert self.node_attributes_children == Node.from_json(self.node_attributes_children_json)
        assert self.node_attributes_no_children == Node.from_json(self.node_attributes_no_children_json)
        assert self.node_children_no_attributes == Node.from_json(self.node_children_no_attributes_json)
        assert self.node_no_attributes_children == Node.from_json(self.node_no_attributes_children_json)

    def test_from_json_incorrect_missing_title(self):
        with pytest.raises(InvalidTreeException):
            Node.from_json(self.node_no_id)

    def test_from_json_incorrect_no_id(self):
        with pytest.raises(InvalidTreeException):
            Node.from_json(self.node_no_title)

    def test_from_json_wrong_types(self):
        with pytest.raises(InvalidTreeException):
            Node.from_json(self.node_wrong_children_type)
        with pytest.raises(InvalidTreeException):
            Node.from_json(self.node_wrong_id_type)
        with pytest.raises(InvalidTreeException):
            Node.from_json(self.node_wrong_title_type)

    def test_add_child(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.add_child("4")
        assert ["2", "3", "4"] == node.children

    def test_remove_child_existent(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.remove_child("2")
        assert ["3"] == node.children

    def test_remove_child_not_existent(self):
        node = Node.from_json(self.node_no_attributes_children_json)
        with pytest.raises(ChildNotFoundException):
            node.remove_child("2")

    def test_add_attribute(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.add_attribute("b", False)
        assert {"a": True, "b": False} == node.attributes

    def test_remove_attribute_existent(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.remove_attribute("a")

    def test_remove_attribute_not_existent(self):
        node = Node.from_json(self.node_no_attributes_children_json)
        with pytest.raises(AttributeNotFoundException):
            node.remove_attribute("a")

    def test_create_json(self):
        assert self.node_attributes_children_json == self.node_attributes_children.create_json()
        assert self.node_attributes_no_children_json == self.node_attributes_no_children.create_json()
        assert self.node_children_no_attributes_json == self.node_children_no_attributes.create_json()
        assert self.node_no_attributes_children_json == self.node_no_attributes_children.create_json()
