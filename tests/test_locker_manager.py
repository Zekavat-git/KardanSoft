import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from core.locker_manager import LockerManager


def print_separator(title):

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_locker(
    manager,
    locker_id
):

    locker = manager.get_locker(
        locker_id
    )

    if locker is None:

        print(
            f"LOCKER | "
            f"Locker={locker_id} | "
            "NOT FOUND"
        )

        return

    print(
        "LOCKER | "
        f"Locker={locker.locker_id} | "
        f"Slave={locker.slave_address} | "
        f"Channel={locker.channel} | "
        f"Actual={locker.actual_state.value} | "
        f"Expected={locker.expected_state.value} | "
        f"Occupancy={locker.occupancy_state.value} | "
        f"Fault={locker.fault.value}"
    )


def main():

    manager = LockerManager()

    # ============================================================
    # SIGNAL MONITORING
    # ============================================================

    manager.openCommandRequested.connect(
        lambda locker_id, slave, channel:
        print(
            f"SIGNAL -> OPEN COMMAND | "
            f"Locker={locker_id}, "
            f"Slave={slave}, "
            f"Channel={channel}"
        )
    )

    manager.lockerFaultDetected.connect(
        lambda locker_id, fault:
        print(
            f"SIGNAL -> FAULT | "
            f"Locker={locker_id}, "
            f"Fault={fault}"
        )
    )

    manager.commandRejected.connect(
        lambda locker_id, reason:
        print(
            f"SIGNAL -> COMMAND REJECTED | "
            f"Locker={locker_id}, "
            f"Reason={reason}"
        )
    )

    manager.lockerChanged.connect(
        lambda locker_id:
        print(
            f"SIGNAL -> LOCKER CHANGED | "
            f"Locker={locker_id}"
        )
    )

    # ============================================================
    # CREATE 3 LOCKERS
    # ============================================================

    manager.add_locker(
        locker_id=1,
        slave_address=1,
        channel=1
    )

    manager.add_locker(
        locker_id=2,
        slave_address=1,
        channel=2
    )

    manager.add_locker(
        locker_id=3,
        slave_address=1,
        channel=3
    )

    # ============================================================
    # INITIAL HARDWARE FEEDBACK
    # ============================================================

    print_separator(
        "INITIAL FEEDBACK"
    )

    manager.process_feedback(
        1,
        False
    )

    manager.process_feedback(
        2,
        False
    )

    manager.process_feedback(
        3,
        False
    )

    print_locker(
        manager,
        1
    )

    print_locker(
        manager,
        2
    )

    print_locker(
        manager,
        3
    )

    # ============================================================
    # TEST 1
    # NORMAL OPEN / CLOSE
    # ============================================================

    print_separator(
        "TEST 1 - NORMAL OPEN AND CLOSE"
    )

    manager.request_open(
        1
    )

    print(
        "Hardware simulation -> "
        "Locker 1 opened"
    )

    manager.process_feedback(
        locker_id=1,
        is_open=True
    )

    print(
        "Hardware simulation -> "
        "Locker 1 closed"
    )

    manager.process_feedback(
        locker_id=1,
        is_open=False
    )

    print_locker(
        manager,
        1
    )

    # ============================================================
    # TEST 2
    # UNEXPECTED OPEN
    # ============================================================

    print_separator(
        "TEST 2 - UNEXPECTED OPEN"
    )

    print(
        "Hardware simulation -> "
        "Locker 2 opened WITHOUT command"
    )

    manager.process_feedback(
        locker_id=2,
        is_open=True
    )

    print_locker(
        manager,
        2
    )

    # ============================================================
    # TEST 3
    # FAILED TO OPEN
    # ============================================================

    print_separator(
        "TEST 3 - FAILED TO OPEN"
    )

    manager.request_open(
        3
    )

    print(
        "Simulation -> "
        "no OPEN feedback received"
    )

    print(
        "Simulation -> "
        "OPEN timeout occurred"
    )

    manager.open_timeout(
        3
    )

    print_locker(
        manager,
        3
    )

    # ============================================================
    # TEST 4
    # REQUEST OPEN FOR NON-EXISTING LOCKER
    # ============================================================

    print_separator(
        "TEST 4 - INVALID LOCKER"
    )

    manager.request_open(
        99
    )

    print_separator(
        "TEST FINISHED"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
