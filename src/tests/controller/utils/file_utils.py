from controller.utils.file_utils import *


def test_read_json():
    file = read_json(Path('json/trees/valid/SimpleTree.json'))
    assert json_file == file


def test_write_json(tmpdir):
    write_json(tmpdir / "test.json", json_file)
    assert read_json(tmpdir / "test.json") == json_file


def test_read_csv():
    file = read_csv(Path('json/config/node_types/conditions.csv'))
    assert csv_file == file


def test_write_csv(tmpdir):
    write_csv(tmpdir / "conditions.csv", csv_file)
    assert read_json(tmpdir / "conditions.csv") == csv_file


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