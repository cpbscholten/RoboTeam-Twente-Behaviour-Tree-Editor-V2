import json
from typing import Any, Dict


def read_json(src: str) -> Dict[str, Any]:
    """
    Reads a JSON file and converts it to a dict
    :param src: the location of the JSON file
    :return: a dict containing the JSON
    """
    with open(src) as data_file:
        data_loaded = json.load(data_file)
    return data_loaded


def write_json(dest: str, content: Dict[str, Any]):
    """
    Writes a dict with JSON to a file
    :param dest: the location of the file
    :param content: the JSON to write in a dict
    """
    with open(dest, 'w') as data_file:
        json.dump(content, data_file, indent=2, sort_keys=True)
