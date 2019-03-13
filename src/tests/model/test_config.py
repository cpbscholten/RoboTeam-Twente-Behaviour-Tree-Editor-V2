from pathlib import Path

import pytest

from controller.utils import read_json, write_json
from model.config import Settings
from model.exceptions import SettingNotFoundException


class TestSettings(object):

    def test_invalid_query(self):
        with pytest.raises(SettingNotFoundException):
            Settings.query_setting("nonexistent", "test")

    def test_valid_query(self):
        assert "json/jsons" == Settings.query_setting("default_json_folder", "test")

    def test_valid_alteration(self, tmpdir):
        # use tmpdir, so we're not overriding the official settings file
        json_settings = read_json(Settings.SETTINGS_PATH)
        tmp_path = tmpdir / 'settings.json'
        write_json(tmp_path, json_settings)
        default_json_folder_path = Path(Settings.default_json_folder())
        Settings.alter_default_json_folder(Path("blahs"))
        assert Settings.default_json_folder() == Path("blahs")
        Settings.alter_default_json_folder(Path(default_json_folder_path))
        assert Settings.default_json_folder() == default_json_folder_path

    def test_valid_alteration_default(self, tmpdir):
        default_json_folder_path = Path(Settings.default_json_folder())
        Settings.alter_default_json_folder(Path("blahs"))
        assert Settings.default_json_folder() == Path("blahs")
        Settings.alter_default_json_folder(default_json_folder_path)
        assert Settings.default_json_folder() == default_json_folder_path

    def test_invalid_alteration(self, tmpdir):
        # use tmpdir, so we're not overriding the official settings file
        json_settings = read_json(Settings.SETTINGS_PATH)
        tmp_path = tmpdir / 'settings.json'
        write_json(tmp_path, json_settings)
        with pytest.raises(SettingNotFoundException):
            Settings.alter_setting("test", "blahs", "test", tmp_path)

    def test_default_jsons_folder(self):
        assert Path('json/jsons') == Settings.default_json_folder()

    def test_default_node_types_folder(self):
        assert Path('json/node_types') == Settings.default_node_types_folder()
