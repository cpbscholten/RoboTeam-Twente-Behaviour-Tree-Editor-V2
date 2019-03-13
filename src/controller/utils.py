import json
import csv
from pathlib import Path
from typing import Any, Dict, List


def read_json(src: Path) -> Dict[str, Any]:
    """
    Reads a JSON file and converts it to a dict
    :param src: the location of the JSON file
    :return: a dict containing the JSON
    """
    with open(str(src), 'r') as data_file:
        data_loaded = json.load(data_file)
    return data_loaded


def write_json(dest: Path, content: Dict[str, Any]):
    """
    Writes a dict with JSON to a file
    :param dest: the location of the file
    :param content: the JSON to write in a dict
    """
    with open(str(dest), 'w') as data_file:
        json.dump(content, data_file, indent=2, sort_keys=True)


def read_csv(src: Path) -> List[List[str]]:
    """
    Reads a csv file, removes blank lines and adds the result to a list
    :param src: the location of the csv file
    :return: a list of lines, with blank lines removed
    """
    with open(str(src), 'r') as f:
        reader = csv.reader(f)
        return list(reader)


def write_csv(dest: Path, content: List[List[str]]):
    """
    Writes a csv file to a given file
    :param dest: the location of the file
    :param content: the content to write in a list
    """
    import csv
    with open(str(dest), 'w') as f:
        writer = csv.writer(f)
        writer.writerows(content)
