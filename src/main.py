import sys

from PyQt5.QtWidgets import QApplication

from model.editor_settings import *
from view.widget.MainWidget import MainWidget

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=query_setting("logfile_name", "main"),
                    filemode='w')

# start UI
app = QApplication(sys.argv)
main_widget = MainWidget()
main_widget.show()
exit_state = app.exec()
sys.exit(exit_state)
