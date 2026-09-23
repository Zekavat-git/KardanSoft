from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Backend(QObject):

    statusChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def testTouch(self):
        print("Touch button pressed from QML")

        self.statusChanged.emit(
            "فرمان لمس توسط سیستم دریافت شد"
        )