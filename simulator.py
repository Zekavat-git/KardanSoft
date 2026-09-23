from PyQt5.QtCore import QObject, pyqtSlot


class Simulator(QObject):

    def __init__(self, app_state):
        super().__init__()

        self.app_state = app_state

    # =========================================================
    # POWER
    # =========================================================

    @pyqtSlot()
    def toggleMainsPower(self):

        new_state = not self.app_state.mainsAvailable

        self.app_state.mainsAvailable = new_state

        # If mains is lost, battery cannot be charging.
        if new_state:
            self.app_state.batteryCharging = True
        else:
            self.app_state.batteryCharging = False

        print(
            "SIMULATOR | Mains:",
            self.app_state.mainsAvailable
        )

    # =========================================================
    # ETHERNET
    # =========================================================

    @pyqtSlot()
    def toggleEthernet(self):

        self.app_state.ethernetConnected = (
            not self.app_state.ethernetConnected
        )

        print(
            "SIMULATOR | Ethernet:",
            self.app_state.ethernetConnected
        )

    # =========================================================
    # BATTERY
    # =========================================================

    @pyqtSlot()
    def normalBattery(self):

        self.app_state.batteryPercent = 86

        print("SIMULATOR | Battery: 86%")

    @pyqtSlot()
    def lowBattery(self):

        self.app_state.batteryPercent = 25

        print("SIMULATOR | Battery: 25%")

    @pyqtSlot()
    def criticalBattery(self):

        self.app_state.batteryPercent = 10

        print("SIMULATOR | Battery: 10%")

    @pyqtSlot()
    def emptyBattery(self):

        self.app_state.batteryPercent = 2

        print("SIMULATOR | Battery: 2%")