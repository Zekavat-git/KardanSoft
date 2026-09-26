import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )

from PyQt5.QtCore import QCoreApplication, QTimer

from core.locker_manager import LockerManager
from hardware.simulator_transport import SimulatorTransport


def main():

    app = QCoreApplication(sys.argv)

    # ============================================================
    # CREATE OBJECTS
    # ============================================================

    manager = LockerManager()
    transport = SimulatorTransport()

    # ============================================================
    # CONNECT APPLICATION <-> HARDWARE
    # ============================================================

    manager.openCommandRequested.connect(
        transport.send_open
    )

    transport.feedbackReceived.connect(
        manager.process_feedback
    )

    # ============================================================
    # CREATE LOCKER
    # ============================================================

    manager.add_locker(
        locker_id=1,
        slave_address=1,
        channel=1
    )

    # Initial hardware status
    manager.process_feedback(
        locker_id=1,
        is_open=False
    )

    # ============================================================
    # MONITOR LOCKER CHANGES
    # ============================================================

    def locker_changed(locker_id):

        locker = manager.get_locker(
            locker_id
        )

        print(
            f"STATE | "
            f"Locker={locker_id} | "
            f"Actual={locker.actual_state.value} | "
            f"Expected={locker.expected_state.value} | "
            f"Fault={locker.fault.value}"
        )

    manager.lockerChanged.connect(
        locker_changed
    )

    # ============================================================
    # START TEST
    # ============================================================

    print()
    print("Sending OPEN request...")
    print()

    manager.request_open(1)

    # ============================================================
    # STOP TEST AFTER 5 SECONDS
    # ============================================================

    QTimer.singleShot(
        5000,
        app.quit
    )

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
