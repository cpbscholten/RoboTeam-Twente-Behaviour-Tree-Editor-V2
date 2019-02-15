from controller.utils.json_utils import *


def test_read_json():
    json = read_json('json/trees/valid/SimpleTree.json')
    assert json == file


def test_write_json(tmpdir):
    write_json(tmpdir / "test.json", file)
    assert read_json(tmpdir / "test.json") == file


file = {
  "name": "SimpleTree",
  "data": {
    "trees": [
      {
        "title": "SimpleTree",
        "root": "1",
        "nodes": {
          "1": {
            "id": "1",
            "title": "Sequence"
          }
        }
      }
    ]
  }
}