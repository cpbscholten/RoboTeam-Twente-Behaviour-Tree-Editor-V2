import os
from pathlib import Path

import pytest

from controller.utils.file_utils import read_json, write_json
from model.config.settings import Settings
from model.exceptions.setting_not_found_exception import SettingNotFoundException


class TestSettings(object):
    def test_invalid_query(self):
        with pytest.raises(SettingNotFoundException):
            Settings.query_setting("nonexistent", "test")

    def test_valid_query(self):
        assert "jsons" == Settings.query_setting("default_json_folder", "test")

    def test_valid_alteration(self, tmpdir):
        # use tmpdir, so we're not overriding the official settings file
        json_settings = read_json(Settings.SETTINGS_PATH)
        tmp_path = tmpdir / 'settings.json'
        write_json(tmp_path, json_settings)
        Settings.alter_setting("default_json_folder", "blahs", "test", tmp_path)
        assert Settings.query_setting("default_json_folder", "test", tmp_path) == "blahs"
        Settings.alter_setting("default_json_folder", "jsons", "test", tmp_path)
        assert Settings.query_setting("default_json_folder", "test", tmp_path) == "jsons"

    def test_valid_alteration_default(self, tmpdir):
        Settings.alter_setting("default_json_folder", "blahs", "test")
        assert Settings.query_setting("default_json_folder", "test") == "blahs"
        Settings.alter_setting("default_json_folder", "jsons", "test")
        assert Settings.query_setting("default_json_folder", "test") == "jsons"

    def test_invalid_alteration(self, tmpdir):
        # use tmpdir, so we're not overriding the official settings file
        json_settings = read_json(Settings.SETTINGS_PATH)
        tmp_path = tmpdir / 'settings.json'
        write_json(tmp_path, json_settings)
        with pytest.raises(SettingNotFoundException):
            Settings.alter_setting("test", "blahs", "test", tmp_path)

    def test_default_jsons_folder(self):
        assert Path('jsons') == Settings.default_json_folder()

    # def test_alter_default_jsons_folder(self, tmpdir):
    #     json_settings = read_json(Settings.SETTINGS_PATH)
    #     tmp_path = tmpdir / 'settings.json'
    #     write_json(tmp_path, json_settings)
    #     Settings.alter
    #     assert

    def test_default_node_types_folder(self):
        assert Path('json/config/node_types') == Settings.default_node_types_folder()
