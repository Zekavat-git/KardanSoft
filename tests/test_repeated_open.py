from PyQt5.QtCore import QCoreApplication

from core.locker_manager import LockerManager
from locker_controller import LockerController


def get_app():

    app = QCoreApplication.instance()

    if app is None:
        app = QCoreApplication([])

    return app


# ============================================================
# MANAGER: EVERY OPEN EXECUTION EMITS A NEW HARDWARE COMMAND
# ============================================================

def test_manager_repeated_open_emits_every_command():

    get_app()

    manager = LockerManager()

    manager.add_locker(
        locker_id=9,
        slave_address=2,
        channel=1
    )

    commands = []

    manager.openCommandRequested.connect(
        lambda locker_id, slave_address, channel:
        commands.append(
            (
                locker_id,
                slave_address,
                channel
            )
        )
    )

    assert manager.request_open(9) is True
    assert manager.request_open(9) is True
    assert manager.request_open(9) is True

    assert commands == [
        (9, 2, 1),
        (9, 2, 1),
        (9, 2, 1),
    ]


# ============================================================
# CONTROLLER: INDEPENDENT REQUESTS MUST NOT BE COLLAPSED
# ============================================================

def test_controller_preserves_repeated_open_requests():

    get_app()

    manager = LockerManager()

    manager.add_locker(
        locker_id=9,
        slave_address=2,
        channel=1
    )

    controller = LockerController(
        manager
    )

    # Do not process the Qt event loop between these calls.
    # We want to inspect the queue exactly as three independent
    # requests arrive.

    assert controller.openLocker(9) is True
    assert controller.openLocker(9) is True
    assert controller.openLocker(9) is True

    assert controller._open_queue == [
        9,
        9,
        9,
    ]
