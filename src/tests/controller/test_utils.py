from controller.utils import *
from model.config import Settings


def test_read_json():
    file = read_json(Path('json/trees/valid/SimpleTree.json'))
    assert json_file == file


def test_write_json(tmpdir):
    write_json(tmpdir / "test.json", json_file)
    assert read_json(tmpdir / "test.json") == json_file


def test_read_csv():
    file = read_csv(Settings.default_node_types_folder() / 'conditions.csv')
    assert csv_file == file


def test_write_csv(tmpdir):
    write_csv(tmpdir / "conditions.csv", csv_file)
    assert read_csv(tmpdir / "conditions.csv") == csv_file


def test_singularize():
    assert "Keeper" == singularize("Keeper")
    assert "Role" == singularize("Roles")
    assert "Strategy" == singularize("Strategies")


def test_capitalize():
    assert "Keeper" == capitalize("keeper")
    assert "Role" == capitalize("Role")
    assert "_" == capitalize("_")


json_file = {
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

csv_file = [
    ["HasBall"],
    ["TheyHaveBall"],
    ["HasBall"],
    ["BallKickedToOurGoal"],
    ["BallInDefenseAreaAndStill"],
    ["IsInDefenseArea"],
    ["IsOnOurSide"],
    ["WeHaveBall"],
    ["IsRobotClosestToBall", "secondsAhead"],
    ["IsBallOnOurSide", "inField"],
    ["IsBeingPassedTo"],
    ["IsCloseToPoint", "ball", "position", "margin"]
]
