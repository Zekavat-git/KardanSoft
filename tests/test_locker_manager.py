from core.locker_manager import LockerManager


def print_separator(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


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
#
# At startup all lockers are initially UNKNOWN.
# We simulate feedback from hardware saying all are CLOSED.
# ============================================================

print_separator("INITIAL FEEDBACK")

manager.process_feedback(1, False)
manager.process_feedback(2, False)
manager.process_feedback(3, False)


manager.print_locker(1)
manager.print_locker(2)
manager.print_locker(3)


# ============================================================
# TEST 1
# NORMAL OPEN / CLOSE
# ============================================================

print_separator("TEST 1 - NORMAL OPEN AND CLOSE")

manager.request_open(1)

print("Hardware simulation -> Locker 1 opened")

manager.process_feedback(
    locker_id=1,
    is_open=True
)

print("Hardware simulation -> Locker 1 closed")

manager.process_feedback(
    locker_id=1,
    is_open=False
)

manager.print_locker(1)


# ============================================================
# TEST 2
# UNEXPECTED OPEN
# ============================================================

print_separator("TEST 2 - UNEXPECTED OPEN")

print(
    "Hardware simulation -> "
    "Locker 2 opened WITHOUT command"
)

manager.process_feedback(
    locker_id=2,
    is_open=True
)

manager.print_locker(2)


# ============================================================
# TEST 3
# FAILED TO OPEN
# ============================================================

print_separator("TEST 3 - FAILED TO OPEN")

manager.request_open(3)

print(
    "Simulation -> no OPEN feedback received"
)

print(
    "Simulation -> OPEN timeout occurred"
)

manager.open_timeout(3)

manager.print_locker(3)


# ============================================================
# TEST 4
# REQUEST OPEN FOR NON-EXISTING LOCKER
# ============================================================

print_separator("TEST 4 - INVALID LOCKER")

manager.request_open(99)


print_separator("TEST FINISHED")