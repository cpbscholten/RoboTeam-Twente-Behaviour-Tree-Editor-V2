import sys

import model.config
from view.applications import Application
from view.windows import MainWindow

if __name__ == '__main__':
    # set up logging
    model.config.Settings.set_up_logging()

    # start UI
    app = Application(sys.argv)
    main_window = MainWindow(app)
    main_window.show()
    exit_state = app.exec()
    sys.exit(exit_state)
