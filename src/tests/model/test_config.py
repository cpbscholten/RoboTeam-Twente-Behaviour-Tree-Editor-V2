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
        assert "json/jsons" == Settings.query_setting("default_json_folder", "test", Settings.SETTINGS_PATH)

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

    def test_alter_default_jsons_folder(self, tmpdir):
        def_path = Settings.default_json_folder()
        Settings.alter_default_json_folder(tmpdir)
        assert tmpdir == Settings.default_json_folder()
        Settings.alter_default_json_folder(def_path)
        assert def_path == Settings.default_json_folder()

    def test_default_node_types_folder(self):
        assert Path('json/node_types') == Settings.default_node_types_folder()

    def test_alter_default_node_types_folder(self, tmpdir):
        def_path = Settings.default_node_types_folder()
        Settings.alter_default_node_types_folder(tmpdir)
        assert tmpdir == Settings.default_node_types_folder()
        Settings.alter_default_node_types_folder(def_path)
        assert def_path == Settings.default_node_types_folder()

    def test_default_id_size(self):
        assert 16 == Settings.default_id_size()

    def test_alter_default_id_size(self):
        def_int = Settings.default_id_size()
        Settings.alter_default_id_size(15)
        assert 15 == Settings.default_id_size()
        Settings.alter_default_id_size(def_int)
        assert def_int == Settings.default_id_size()

    def test_default_logfile_name(self):
        assert "log" == Settings.default_logfile_name()

    def test_alter_default_logfile_name(self, tmpdir):
        def_path = Settings.default_logfile_name()
        Settings.alter_default_logfile_name(tmpdir / "log")
        assert tmpdir / "log" == Settings.default_logfile_name()
        Settings.alter_default_logfile_name(def_path)
        assert def_path == Settings.default_logfile_name()

    def test_set_up_logging(self):
        # check that it runs without exceptions
        Settings.set_up_logging()
