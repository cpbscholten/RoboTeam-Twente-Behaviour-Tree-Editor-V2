from controller.utils.json_utils import *
import logging

settings = read_json('config/settings.json')
logger = logging.getLogger("main")


def query_setting(setting, caller):
    """
    Queries for setting values by setting name.
    :param setting: String name of the setting to be queried
    :param caller: String name for the part of the program calling this method
    :return: The value of the queried setting
    """
    if setting not in settings.keys():
        # If the setting doesn't exist, log the error and return None
        logger.error("Invalid setting " + "\'" + setting + "\'" + " queried by " + caller + ".")
        return
    return settings[setting]


def alter_setting(setting, val, caller):
    """
    Finds a setting by name and changes it to the given value.
    :param setting: String name of the setting to be altered
    :param val: String for the desired value of the setting
    :param caller: String name for the part of the program calling this method
    """
    if setting not in settings.keys():
        # If the setting doesn't exist, log the error and change nothing
        logger.error("Invalid setting " + "\'" + setting + "\'" + " accessed by " + caller + ".")
        return
    # Update the corresponding setting in the settings dict and also the settings JSON
    settings[setting] = val
    write_json('settings.json', settings)
