from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal


class AppState(QObject):

    ethernetConnectedChanged = pyqtSignal()
    mainsAvailableChanged = pyqtSignal()
    batteryPercentChanged = pyqtSignal()
    batteryChargingChanged = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Initial simulated values
        self._ethernet_connected = True
        self._mains_available = True
        self._battery_percent = 86
        self._battery_charging = True

    # =========================================================
    # ETHERNET
    # =========================================================

    def get_ethernet_connected(self):
        return self._ethernet_connected

    def set_ethernet_connected(self, value):
        value = bool(value)

        if self._ethernet_connected == value:
            return

        self._ethernet_connected = value
        self.ethernetConnectedChanged.emit()

    ethernetConnected = pyqtProperty(
        bool,
        fget=get_ethernet_connected,
        fset=set_ethernet_connected,
        notify=ethernetConnectedChanged
    )

    # =========================================================
    # MAINS POWER
    # =========================================================

    def get_mains_available(self):
        return self._mains_available

    def set_mains_available(self, value):
        value = bool(value)

        if self._mains_available == value:
            return

        self._mains_available = value
        self.mainsAvailableChanged.emit()

    mainsAvailable = pyqtProperty(
        bool,
        fget=get_mains_available,
        fset=set_mains_available,
        notify=mainsAvailableChanged
    )

    # =========================================================
    # BATTERY PERCENT
    # =========================================================

    def get_battery_percent(self):
        return self._battery_percent

    def set_battery_percent(self, value):
        value = int(value)

        # Keep percentage inside 0–100
        value = max(0, min(100, value))

        if self._battery_percent == value:
            return

        self._battery_percent = value
        self.batteryPercentChanged.emit()

    batteryPercent = pyqtProperty(
        int,
        fget=get_battery_percent,
        fset=set_battery_percent,
        notify=batteryPercentChanged
    )

    # =========================================================
    # BATTERY CHARGING
    # =========================================================

    def get_battery_charging(self):
        return self._battery_charging

    def set_battery_charging(self, value):
        value = bool(value)

        if self._battery_charging == value:
            return

        self._battery_charging = value
        self.batteryChargingChanged.emit()

    batteryCharging = pyqtProperty(
        bool,
        fget=get_battery_charging,
        fset=set_battery_charging,
        notify=batteryChargingChanged
    )