from PyQt5.QtCore import QObject, pyqtSignal


class Transport(QObject):

    # =========================================================
    # SIGNALS FROM HARDWARE TO APPLICATION
    # =========================================================

    # locker_id
    # is_open
    feedbackReceived = pyqtSignal(int, bool)

    # slave_address
    # error message
    communicationError = pyqtSignal(int, str)


    def __init__(self):
        super().__init__()


    # =========================================================
    # COMMAND FROM APPLICATION TO HARDWARE
    # =========================================================

    def send_open(
        self,
        locker_id: int,
        slave_address: int,
        channel: int
    ):
        raise NotImplementedError