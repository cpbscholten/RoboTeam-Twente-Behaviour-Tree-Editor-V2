import logging
from pathlib import Path, PurePosixPath
from typing import Any, Dict

from controller.utils import read_json, write_json
from model.exceptions import SettingNotFoundException


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
        if not path:
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
        if not path:
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
        return Path(Settings.query_setting('default_node_types_folder', 'settings'))

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
        return Path(Settings.query_setting("default_json_folder", "settings"))

    @staticmethod
    def alter_default_json_folder(path: Path):
        """
        Alters the default_jsons_folder setting to the posix path of the provided path avriable
        :param path: path object containing the location of the json directory
        """
        Settings.alter_setting("default_json_folder", PurePosixPath(path).as_posix(), "settings")

    @staticmethod
    def auto_update_roles() -> bool:
        return Settings.query_setting('auto_update_roles', 'settings')

    @staticmethod
    def alter_auto_update_roles(enable: bool):
        """
        Method to update the setting if the roles should be updated automatically.
        :param enable: enable or disable the setting
        """
        Settings.alter_setting("auto_update_roles", enable, 'settings')

    @staticmethod
    def default_collection_categories():
        """
        Queries the default collection categories
        """
        return Settings.query_setting("default_collection_categories", "settings")

    @staticmethod
    def default_id_size():
        """
        Queries the default id size
        """
        return Settings.query_setting("default_id_size", "settings")

    @staticmethod
    def alter_default_id_size(int_size: int):
        """
        Updates the int size used for creating id's of nodes
        :param int_size: the size of the id's of the nodes
        """
        Settings.alter_setting("default_id_size", int_size, "settings")

    @staticmethod
    def default_logfile_name():
        """
        Queries the location logfile in the settings
        """
        return Settings.query_setting("logfile_name", "settings")

    @staticmethod
    def alter_default_logfile_name(path: Path):
        """
        Alters the location of the logfile
        :param path: the path + filename of the logfile
        """
        Settings.alter_setting('logfile_name', PurePosixPath(path).as_posix(), 'settings')
        Settings.set_up_logging()

    @staticmethod
    def set_up_logging():
        """
        Method that loads the logging settings and set up logging to the specified file
        """
        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # set up the logging
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=Settings.default_logfile_name(),
                            filemode='a')
