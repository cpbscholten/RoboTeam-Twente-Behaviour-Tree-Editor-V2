import logging
import sys

from PyQt5.QtWidgets import QApplication

import model.config.settings
import view.windows


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=model.config.settings.Settings.query_setting("logfile_name", "main"),
                        filemode='w')

    # start UI
    app = QApplication(sys.argv)
    main_widget = view.windows.MainWindow()
    main_widget.show()
    exit_state = app.exec()
    sys.exit(exit_state)
