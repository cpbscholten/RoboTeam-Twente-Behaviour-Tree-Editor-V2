from model.editor_settings import *
from model.exceptions.SettingNotFoundException import SettingNotFoundException
import pytest


def test_invalid_query():
    with pytest.raises(SettingNotFoundException):
        assert query_setting("nonexistent", "test")


def test_valid_query():
    assert query_setting("default_json_folder", "test") == "jsons"


def test_valid_alteration():
    alter_setting("default_json_folder", "blahs", "test")
    assert query_setting("default_json_folder", "test") == "blahs"
    alter_setting("default_json_folder", "jsons", "test")
    assert query_setting("default_json_folder", "test") == "jsons"


def test_invalid_alteration():
    with pytest.raises(SettingNotFoundException):
        alter_setting("blah", "blah", "test")
