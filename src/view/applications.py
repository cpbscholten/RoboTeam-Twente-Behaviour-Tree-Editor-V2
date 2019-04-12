from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QMouseEvent, QIcon
from PyQt5.QtWidgets import QApplication, QGraphicsView, QPushButton

from view.scenes import TreeScene


class Application(QApplication):
    """"
    Custom application only used to set and reset the global cross cursor used when adding nodes
    """

    def __init__(self, sys_args):
        """
        Constructor of the Qt Application
        :param sys_args: System arguments given on start
        """
        super(Application, self).__init__(sys_args)
        self.setApplicationName('RoboTeam Behaviour Tree Editor')
        self.setApplicationDisplayName('RoboTeam Behaviour Tree Editor')
        self.setApplicationVersion('2.0')
        self.setWindowIcon(QIcon('view/icon/appicon.png'))
        self.wait_for_click_filter = None

    def add_cross_cursor(self, scene: TreeScene):
        """
        Sets cross cursor and installs filter
        :param scene: Tree scene
        """
        # remove old filter
        if self.wait_for_click_filter:
            self.removeEventFilter(self.wait_for_click_filter)
        # Set cross cursor
        self.setOverrideCursor(Qt.CrossCursor)
        # Install new filter
        self.wait_for_click_filter = ResetCursorAfterClick(self, scene)
        self.installEventFilter(self.wait_for_click_filter)


class ResetCursorAfterClick(QObject):
    
    def __init__(self, app, scene: TreeScene, parent=None):
        """
        Constructor of ResetCursorAfterClick event filter
        :param app: The Qt application
        :param scene: The tree scene
        :param parent: Parent of this object
        """
        super(ResetCursorAfterClick, self).__init__(parent)
        self.app = app
        self.scene = scene

    def eventFilter(self, filter_object, event):
        """
        Event filter that detects mouse click outside of tree scene and resets cursor in that case.
        :param filter_object: Object related to the event
        :param event: Event that occurred
        :return: If the event needs to be suppressed
        """
        # widget currently focused
        focus_widget = self.app.focusWidget()
        if isinstance(event, QMouseEvent) and not (isinstance(focus_widget, QGraphicsView)
                                                   or isinstance(focus_widget, QPushButton)):
            if self.scene.adding_node and (event.button() == Qt.LeftButton or event.button() == Qt.RightButton):
                self.reset_event_filter()
                return True
        return False

    def reset_event_filter(self):
        """
        Stops node addition and resets cursor
        """
        # reset adding node state of the scene
        self.scene.adding_node = None
        # reset cursor and remove filter
        self.app.restoreOverrideCursor()
        self.app.removeEventFilter(self)
