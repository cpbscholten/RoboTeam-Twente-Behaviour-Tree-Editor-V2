from model.editor_settings import *


def test_invalid_query():
    assert query_setting("nonexistent", "test") is None


def test_valid_query():
    assert query_setting("default_json_folder", "test") == "jsons"


def test_valid_alteration():
    alter_setting("default_json_folder", "blahs", "test")
    assert query_setting("default_json_folder", "test") == "blahs"
    alter_setting("default_json_folder", "jsons", "test")
    assert query_setting("default_json_folder", "test") == "jsons"


test_invalid_query()
test_valid_query()
test_valid_alteration()
