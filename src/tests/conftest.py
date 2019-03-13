import pytest

from model.config import Settings


@pytest.fixture(autouse=True, scope="session")
def path_fixture():
    """
    Runs once at every session at sets the
    default paths for custom test config files
    """
    Settings.SETTINGS_PATH = 'json/config/settings.json'
