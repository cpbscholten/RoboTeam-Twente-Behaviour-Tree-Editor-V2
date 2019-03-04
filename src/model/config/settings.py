from pathlib import Path, PurePosixPath
from typing import Any, Dict

from controller.utils.file_utils import read_json, write_json
import logging

from model.exceptions.setting_not_found_exception import SettingNotFoundException


class Settings:
    """
    Global class for storing the path of the settings file.
    In a class to allow external modification
    """
    SETTINGS_PATH: Path = Path('config/settings.json')
    logger = logging.getLogger("settings")

    @staticmethod
    def query_setting(setting: str, caller: str, path: Path = None) -> Any:
        """
        Queries for setting values by setting name.
        :param setting: String name of the setting to be queried
        :param caller: String name for the part of the program calling this method
        :param path: for overriding the default settings path
        :raises SettingNotFoundException: When the requested setting does not exist
        :return: The value of the queried setting
        """
        # set path default value when not initialized
        if path is None:
            path = Settings.SETTINGS_PATH
        settings: Dict[str, Any] = read_json(path)
        if setting not in settings.keys():
            # If the setting doesn't exist, log the error and return None
            Settings.logger.error("Invalid setting " + "\'" + setting + "\'" + " queried by " + caller + ".")
            raise SettingNotFoundException
        return settings[setting]

    @staticmethod
    def alter_setting(setting: str, val: Any, caller: str, path: Path = None):
        """
        Finds a setting by name and changes it to the given value.
        :param setting: String name of the setting to be altered
        :param val: String for the desired value of the setting
        :param caller: String name for the part of the program calling this method
        :raises SettingNotFoundException: When the requested setting does not exist
        :param path for overriding the default settings path
        """
        # set path default value when not initialized
        if path is None:
            path = Settings.SETTINGS_PATH
        settings: Dict[str, Any] = read_json(path)
        if setting not in settings.keys():
            # If the setting doesn't exist, log the error and change nothing
            Settings.logger.error("Invalid setting " + "\'" + setting + "\'" + " accessed by " + caller + ".")
            raise SettingNotFoundException
        # Update the corresponding setting in the settings dict and also the settings JSON
        settings[setting] = val
        write_json(path, settings)

    @staticmethod
    def default_node_types_folder() -> Path:
        """
        Reads the default_node_types setting and returns a path variable from it
        :return: a path variable containing the path to node_types
        """
        path = Settings.query_setting('default_node_types_folder', 'settings')
        return Path(path)

    @staticmethod
    def alter_default_node_types_folder(path: Path):
        """
        Alters the default_node_types setting to the posix path of the provided path avriable
        :param path: path object containing the location of the node_types directory
        """
        Settings.alter_setting('default_node_types_folder', PurePosixPath(path).as_posix(), 'settings')

    @staticmethod
    def default_json_folder() -> Path:
        """
        Reads the default_jsons_folder setting and returns a path variable from it
        :return: a path variable containing the path to the jsons fodler
        """
        path = Settings.query_setting("default_json_folder", "settings")
        return Path(path)

    @staticmethod
    def alter_default_json_folder(path: Path):
        """
        Alters the default_jsons_folder setting to the posix path of the provided path avriable
        :param path: path object containing the location of the json directory
        """
        Settings.alter_setting("default_json_folder", PurePosixPath(path).as_posix(), "settings")
