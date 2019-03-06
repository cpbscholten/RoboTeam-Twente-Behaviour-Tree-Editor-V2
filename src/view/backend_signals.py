from PyQt5.QtCore import pyqtSignal, QObject


class BackendSignals(QObject):
    connect = pyqtSignal(object)


Signals = BackendSignals()
