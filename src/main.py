import logging
import sys

from PyQt5.QtWidgets import QApplication

from model.config.settings import Settings
from view.widget.main_widget import MainWidget

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=Settings.query_setting("logfile_name", "main"),
                    filemode='w')

# start UI
app = QApplication(sys.argv)
main_widget = MainWidget()
main_widget.show()
exit_state = app.exec()
sys.exit(exit_state)
