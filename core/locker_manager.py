import time

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)

from core.locker import (
    ExpectedState,
    Locker,
    LockerFault,
    LockerState,
    OccupancyState,
)


class LockerManager(QObject):

    lockerChanged = pyqtSignal(int)

    # Emitted around structural changes so QAbstractListModel can
    # reset safely when the number/mapping of lockers changes.
    lockerStructureAboutToChange = pyqtSignal()
    lockerStructureChanged = pyqtSignal()

    lockerFaultDetected = pyqtSignal(
        int,
        str
    )

    openCommandRequested = pyqtSignal(
        int,
        int,
        int
    )

    commandRejected = pyqtSignal(
        int,
        str
    )

    def __init__(self, database=None):
        super().__init__()

        self._database = database

        self._lockers = {}

        # Tracks lockers that actually reached OPEN after our command.
        self._opened_since_command = set()

    # =========================================================
    # LOCKER REGISTRY
    # =========================================================

    def add_locker(
        self,
        locker_id: int,
        slave_address: int,
        channel: int
    ):

        locker_id = int(locker_id)

        if locker_id in self._lockers:
            raise ValueError(
                f"Locker {locker_id} already exists."
            )

        locker = Locker(
            locker_id=locker_id,
            slave_address=int(slave_address),
            channel=int(channel)
        )

        # Restore only persistent assignment/business state.
        # Physical state must still come from fresh hardware feedback.
        if self._database is not None:

            assignment = (
                self._database.get_assignment(
                    locker_id
                )
            )

            if assignment is not None:

                locker.occupancy_state = (
                    OccupancyState.OCCUPIED
                )

                locker.assigned_to = (
                    assignment["assigned_to"]
                )

                locker.assigned_at = (
                    assignment["assigned_at"]
                )

        self._lockers[locker_id] = locker

    def get_locker(
        self,
        locker_id: int
    ):

        return self._lockers.get(
            int(locker_id)
        )

    def get_all_lockers(self):

        return [
            self._lockers[locker_id]
            for locker_id
            in sorted(self._lockers)
        ]

    # =========================================================
    # DYNAMIC LOCKER CONFIGURATION
    # =========================================================

    @pyqtSlot(
        str,
        result=bool
    )
    def configureLockersCsv(
        self,
        active_channels_csv: str
    ):

        try:

            channel_counts = [
                int(value.strip())
                for value
                in active_channels_csv.split(",")
                if value.strip() != ""
            ]

        except (
            TypeError,
            ValueError
        ):

            print(
                "LOCKER CONFIG | REJECTED | "
                "Invalid channel CSV"
            )

            return False

        if (
            len(channel_counts) < 1
            or len(channel_counts) > 32
        ):

            print(
                "LOCKER CONFIG | REJECTED | "
                "Slave count must be 1..32"
            )

            return False

        if any(
            count < 0
            or count > 12
            for count in channel_counts
        ):

            print(
                "LOCKER CONFIG | REJECTED | "
                "Each slave must use 0..12 channels"
            )

            return False

        total_lockers = sum(
            channel_counts
        )

        if total_lockers < 1:

            print(
                "LOCKER CONFIG | REJECTED | "
                "At least one locker is required"
            )

            return False

        # Do not remap physical lockers while an OPEN command is
        # still pending.
        for locker in self._lockers.values():

            if (
                locker.expected_state
                == ExpectedState.OPEN
            ):

                print(
                    "LOCKER CONFIG | REJECTED | "
                    "An open command is still active"
                )

                return False

        old_by_hardware = {
            (
                locker.slave_address,
                locker.channel
            ):
                locker
            for locker
            in self._lockers.values()
        }

        self.lockerStructureAboutToChange.emit()

        self._lockers = {}
        self._opened_since_command.clear()

        next_locker_id = 1

        for (
            slave_index,
            active_count
        ) in enumerate(
            channel_counts,
            start=1
        ):

            for channel in range(
                1,
                active_count + 1
            ):

                self.add_locker(
                    locker_id=next_locker_id,
                    slave_address=slave_index,
                    channel=channel
                )

                new_locker = (
                    self._lockers[
                        next_locker_id
                    ]
                )

                old_locker = (
                    old_by_hardware.get(
                        (
                            slave_index,
                            channel
                        )
                    )
                )

                # Preserve live hardware state for physical
                # channels that already existed. Persistent
                # assignment data is restored by add_locker()
                # from SQLite using the current global locker ID.
                if old_locker is not None:

                    new_locker.actual_state = (
                        old_locker.actual_state
                    )

                    new_locker.expected_state = (
                        old_locker.expected_state
                    )

                    new_locker.fault = (
                        old_locker.fault
                    )

                    new_locker.last_command = (
                        old_locker.last_command
                    )

                    new_locker.last_command_time = (
                        old_locker.last_command_time
                    )

                    new_locker.last_feedback_time = (
                        old_locker.last_feedback_time
                    )

                next_locker_id += 1

        self.lockerStructureChanged.emit()

        print(
            "LOCKER CONFIG | APPLIED | "
            f"Slaves={len(channel_counts)} | "
            f"Channels={channel_counts} | "
            f"TotalLockers={total_lockers}"
        )

        return True

    # =========================================================
    # OCCUPANCY / ASSIGNMENT STATE
    # =========================================================

    def assign_locker(
        self,
        locker_id: int,
        assigned_to=None
    ) -> bool:

        locker = self.get_locker(
            locker_id
        )

        if locker is None:
            return False

        if (
            self._database is not None
        ):

            self._database.assign_locker(
                locker_id,
                assigned_to
            )

            assignment = (
                self._database.get_assignment(
                    locker_id
                )
            )

        else:

            assignment = {
                "assigned_to":
                    assigned_to,

                "assigned_at":
                    None,
            }

        changed = (
            locker.occupancy_state
            != OccupancyState.OCCUPIED
            or
            locker.assigned_to
            != assignment["assigned_to"]
            or
            locker.assigned_at
            != assignment["assigned_at"]
        )

        locker.occupancy_state = (
            OccupancyState.OCCUPIED
        )

        locker.assigned_to = (
            assignment["assigned_to"]
        )

        locker.assigned_at = (
            assignment["assigned_at"]
        )

        print(
            "ASSIGNMENT | "
            f"Locker={locker.locker_id} | "
            "State=occupied | "
            f"AssignedTo={locker.assigned_to}"
        )

        if changed:

            self.lockerChanged.emit(
                locker.locker_id
            )

        return True

    def release_locker(
        self,
        locker_id: int
    ) -> bool:

        locker = self.get_locker(
            locker_id
        )

        if locker is None:
            return False

        if (
            self._database is not None
        ):

            self._database.release_locker(
                locker_id
            )

        changed = (
            locker.occupancy_state
            != OccupancyState.FREE
            or
            locker.assigned_to is not None
            or
            locker.assigned_at is not None
        )

        locker.occupancy_state = (
            OccupancyState.FREE
        )

        locker.assigned_to = None
        locker.assigned_at = None

        print(
            "ASSIGNMENT | "
            f"Locker={locker.locker_id} | "
            "State=free"
        )

        if changed:

            self.lockerChanged.emit(
                locker.locker_id
            )

        return True

    @pyqtSlot(
        int,
        str,
        result=bool
    )
    def assignLocker(
        self,
        locker_id: int,
        assigned_to: str
    ):

        return self.assign_locker(
            locker_id,
            assigned_to
        )

    @pyqtSlot(
        int,
        result=bool
    )
    def releaseLocker(
        self,
        locker_id: int
    ):

        return self.release_locker(
            locker_id
        )

    # Compatibility helpers used by the current development UI.
    @pyqtSlot(
        int,
        result=bool
    )
    def setLockerOccupied(
        self,
        locker_id: int
    ):

        return self.assign_locker(
            locker_id,
            None
        )

    @pyqtSlot(
        int,
        result=bool
    )
    def setLockerFree(
        self,
        locker_id: int
    ):

        return self.release_locker(
            locker_id
        )

    # =========================================================
    # TCP / EXTERNAL BUSINESS OPERATIONS
    # =========================================================

    def allocate_to_person(
        self,
        locker_id: int,
        person_id: str
    ):
        """
        Strict assignment operation intended for TCP/external commands.

        Returns:
            (success: bool, result_code: str)
        """

        person_id = str(
            person_id
        ).strip()

        if not person_id:

            return (
                False,
                "invalid_person_id"
            )

        locker = self.get_locker(
            locker_id
        )

        if locker is None:

            return (
                False,
                "locker_not_found"
            )

        # -----------------------------------------------------
        # LOCKER ALREADY OCCUPIED
        # -----------------------------------------------------

        if (
            locker.occupancy_state
            == OccupancyState.OCCUPIED
        ):

            # Treat an exact repeat as an idempotent success.
            if locker.assigned_to == person_id:

                return (
                    True,
                    "already_allocated"
                )

            return (
                False,
                "locker_already_allocated"
            )

        # -----------------------------------------------------
        # PERSON ALREADY HAS ANOTHER LOCKER
        # -----------------------------------------------------

        if self._database is not None:

            existing = (
                self._database.find_by_assigned_to(
                    person_id
                )
            )

            if existing is not None:

                if (
                    int(existing["locker_id"])
                    != locker.locker_id
                ):

                    return (
                        False,
                        "person_already_allocated"
                    )

        # -----------------------------------------------------
        # WRITE ASSIGNMENT
        # -----------------------------------------------------

        if self._database is not None:

            self._database.assign_locker(
                locker.locker_id,
                person_id
            )

            assignment = (
                self._database.get_assignment(
                    locker.locker_id
                )
            )

        else:

            assignment = {
                "assigned_to":
                    person_id,

                "assigned_at":
                    None,
            }

        locker.occupancy_state = (
            OccupancyState.OCCUPIED
        )

        locker.assigned_to = (
            assignment["assigned_to"]
        )

        locker.assigned_at = (
            assignment["assigned_at"]
        )

        self.lockerChanged.emit(
            locker.locker_id
        )

        print(
            "TCP BUSINESS | ALLOCATE | "
            f"Locker={locker.locker_id} | "
            f"Person={person_id} | "
            "Result=allocated"
        )

        return (
            True,
            "allocated"
        )


    def release_from_person(
        self,
        locker_id: int,
        person_id: str
    ):
        """
        Strict release operation intended for TCP/external commands.

        The received person_id must match the assignment.

        Returns:
            (success: bool, result_code: str)
        """

        person_id = str(
            person_id
        ).strip()

        if not person_id:

            return (
                False,
                "invalid_person_id"
            )

        locker = self.get_locker(
            locker_id
        )

        if locker is None:

            return (
                False,
                "locker_not_found"
            )

        # Repeated RELEASE of an already-free locker is harmless.
        if (
            locker.occupancy_state
            == OccupancyState.FREE
        ):

            return (
                True,
                "already_free"
            )

        # Never release another person's locker.
        if locker.assigned_to != person_id:

            return (
                False,
                "assignment_mismatch"
            )

        if self._database is not None:

            if not self._database.assignment_matches(
                locker.locker_id,
                person_id
            ):

                return (
                    False,
                    "assignment_mismatch"
                )

            self._database.release_locker(
                locker.locker_id
            )

        locker.occupancy_state = (
            OccupancyState.FREE
        )

        locker.assigned_to = None
        locker.assigned_at = None

        self.lockerChanged.emit(
            locker.locker_id
        )

        print(
            "TCP BUSINESS | RELEASE | "
            f"Locker={locker.locker_id} | "
            f"Person={person_id} | "
            "Result=released"
        )

        return (
            True,
            "released"
        )


    # =========================================================
    # OPEN COMMAND
    # =========================================================

    def request_open(
        self,
        locker_id: int
    ) -> bool:

        locker = self.get_locker(
            locker_id
        )

        if locker is None:

            reason = "locker_not_found"

            self.commandRejected.emit(
                int(locker_id),
                reason
            )

            return False

        locker.expected_state = (
            ExpectedState.OPEN
        )

        locker.last_command = "open"

        locker.last_command_time = (
            time.monotonic()
        )

        locker.fault = LockerFault.NONE

        self._opened_since_command.discard(
            locker.locker_id
        )

        self.lockerChanged.emit(
            locker.locker_id
        )

        self.openCommandRequested.emit(
            locker.locker_id,
            locker.slave_address,
            locker.channel
        )

        return True

    # =========================================================
    # PHYSICAL FEEDBACK
    # =========================================================

    @pyqtSlot(
        int,
        bool
    )
    def process_feedback(
        self,
        locker_id: int,
        is_open: bool
    ):

        locker = self.get_locker(
            locker_id
        )

        if locker is None:
            return

        previous_state = (
            locker.actual_state
        )

        previous_expected = (
            locker.expected_state
        )

        previous_fault = (
            locker.fault
        )

        locker.actual_state = (
            LockerState.OPEN
            if is_open
            else LockerState.CLOSED
        )

        locker.last_feedback_time = (
            time.monotonic()
        )

        fault_event = None

        # -----------------------------------------------------
        # OPEN feedback
        # -----------------------------------------------------

        if (
            locker.actual_state
            == LockerState.OPEN
        ):

            if (
                locker.expected_state
                == ExpectedState.OPEN
            ):

                self._opened_since_command.add(
                    locker.locker_id
                )

                locker.fault = (
                    LockerFault.NONE
                )

            else:

                locker.fault = (
                    LockerFault.UNEXPECTED_OPEN
                )

                if (
                    previous_fault
                    != LockerFault.UNEXPECTED_OPEN
                ):
                    fault_event = (
                        LockerFault.UNEXPECTED_OPEN
                    )

        # -----------------------------------------------------
        # CLOSED feedback
        # -----------------------------------------------------

        else:

            if (
                locker.expected_state
                == ExpectedState.OPEN
                and
                locker.locker_id
                in self._opened_since_command
            ):

                # A commanded opening happened and the user has
                # closed the door again. The operation is complete.
                self._opened_since_command.discard(
                    locker.locker_id
                )

                locker.expected_state = (
                    ExpectedState.CLOSED
                )

                locker.fault = (
                    LockerFault.NONE
                )

            elif (
                locker.fault
                == LockerFault.UNEXPECTED_OPEN
            ):

                # The unexpected physical opening has ended.
                locker.fault = (
                    LockerFault.NONE
                )

        print(
            "FEEDBACK | "
            f"Locker={locker.locker_id} | "
            f"Previous={previous_state.value} | "
            f"Current={locker.actual_state.value} | "
            f"Expected={locker.expected_state.value} | "
            f"Fault={locker.fault.value}"
        )

        changed = (
            previous_state
            != locker.actual_state
            or
            previous_expected
            != locker.expected_state
            or
            previous_fault
            != locker.fault
        )

        if changed:

            self.lockerChanged.emit(
                locker.locker_id
            )

        if fault_event is not None:

            self.lockerFaultDetected.emit(
                locker.locker_id,
                fault_event.value
            )

    # =========================================================
    # OPEN TIMEOUT
    # =========================================================

    def open_timeout(
        self,
        locker_id: int
    ):

        locker = self.get_locker(
            locker_id
        )

        if locker is None:
            return

        if (
            locker.expected_state
            != ExpectedState.OPEN
        ):
            return

        if (
            locker.actual_state
            == LockerState.OPEN
        ):
            return

        previous_fault = (
            locker.fault
        )

        locker.expected_state = (
            ExpectedState.CLOSED
        )

        locker.fault = (
            LockerFault.FAILED_TO_OPEN
        )

        self._opened_since_command.discard(
            locker.locker_id
        )

        print(
            "FAULT | "
            f"Locker={locker.locker_id} | "
            "FAILED_TO_OPEN"
        )

        self.lockerChanged.emit(
            locker.locker_id
        )

        if (
            previous_fault
            != LockerFault.FAILED_TO_OPEN
        ):

            self.lockerFaultDetected.emit(
                locker.locker_id,
                LockerFault.FAILED_TO_OPEN.value
            )
