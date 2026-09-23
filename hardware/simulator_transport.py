from PyQt5.QtCore import QTimer, pyqtSlot

from hardware.transport import Transport


class SimulatorTransport(Transport):

    def __init__(self):
        super().__init__()

        # Delay between command and opening feedback
        self.open_delay_ms = 400

        # How long the simulated door stays open
        self.close_delay_ms = 2500

        # If True, the next OPEN command will not generate OPEN feedback
        self.fail_next_open = False


    # =========================================================
    # NORMAL OPEN COMMAND
    # =========================================================

    @pyqtSlot(int, int, int)
    def send_open(
        self,
        locker_id: int,
        slave_address: int,
        channel: int
    ):

        print(
            f"SIM TRANSPORT | OPEN COMMAND | "
            f"Locker={locker_id} | "
            f"Slave={slave_address} | "
            f"Channel={channel}"
        )

        # -----------------------------------------------------
        # Simulate failure
        # -----------------------------------------------------

        if self.fail_next_open:

            print(
                f"SIM TRANSPORT | "
                f"Locker {locker_id} will NOT open."
            )

            self.fail_next_open = False

            return

        # -----------------------------------------------------
        # OPEN feedback
        # -----------------------------------------------------

        QTimer.singleShot(
            self.open_delay_ms,
            lambda locker_id=locker_id:
            self._simulate_open(locker_id)
        )

        # -----------------------------------------------------
        # CLOSED feedback
        # -----------------------------------------------------

        QTimer.singleShot(
            self.open_delay_ms + self.close_delay_ms,
            lambda locker_id=locker_id:
            self._simulate_close(locker_id)
        )


    # =========================================================
    # INTERNAL SIMULATION
    # =========================================================

    def _simulate_open(self, locker_id: int):

        print(
            f"SIM TRANSPORT | "
            f"Locker {locker_id} OPENED"
        )

        self.feedbackReceived.emit(
            locker_id,
            True
        )


    def _simulate_close(self, locker_id: int):

        print(
            f"SIM TRANSPORT | "
            f"Locker {locker_id} CLOSED"
        )

        self.feedbackReceived.emit(
            locker_id,
            False
        )


    # =========================================================
    # QML - FAIL NEXT COMMAND
    # =========================================================

    @pyqtSlot()
    def failNextCommand(self):

        print(
            "SIM TRANSPORT | "
            "Next OPEN command will fail"
        )

        self.fail_next_open = True


    # =========================================================
    # QML - FORCE OPEN
    # =========================================================

    @pyqtSlot(int)
    def forceOpen(self, locker_id: int):

        print(
            f"SIM TRANSPORT | "
            f"FORCED OPEN | Locker={locker_id}"
        )

        self.feedbackReceived.emit(
            locker_id,
            True
        )


    # =========================================================
    # QML - FORCE CLOSE
    # =========================================================

    @pyqtSlot(int)
    def forceClose(self, locker_id: int):

        print(
            f"SIM TRANSPORT | "
            f"FORCED CLOSE | Locker={locker_id}"
        )

        self.feedbackReceived.emit(
            locker_id,
            False
        )