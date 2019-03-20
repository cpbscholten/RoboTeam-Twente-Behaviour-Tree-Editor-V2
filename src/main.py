import sys

from PyQt5.QtWidgets import QApplication

import model.config

import view.windows


if __name__ == '__main__':
    # set up logging
    model.config.Settings.set_up_logging()

    # start UI
    app = QApplication(sys.argv)
    main_widget = view.windows.MainWindow()
    main_widget.show()
    exit_state = app.exec()
    sys.exit(exit_state)
