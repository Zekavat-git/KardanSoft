import sys

from PyQt5.QtCore import QCoreApplication, QTimer

from core.locker_manager import LockerManager
from hardware.simulator_transport import SimulatorTransport


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

    locker = manager.get_locker(locker_id)

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


sys.exit(app.exec_())