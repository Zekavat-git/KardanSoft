from PyQt5.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    pyqtProperty,
    pyqtSignal,
)


class LockerListModel(QAbstractListModel):

    LockerIdRole = Qt.UserRole + 1
    SlaveAddressRole = Qt.UserRole + 2
    ChannelRole = Qt.UserRole + 3
    ActualStateRole = Qt.UserRole + 4
    ExpectedStateRole = Qt.UserRole + 5
    FaultRole = Qt.UserRole + 6
    OccupancyStateRole = Qt.UserRole + 7
    AssignedToRole = Qt.UserRole + 8
    AssignedAtRole = Qt.UserRole + 9

    summaryChanged = pyqtSignal()

    def __init__(self, manager):
        super().__init__()

        self._manager = manager

        self._lockers = (
            self._manager.get_all_lockers()
        )

        self._summary_cache = (
            self._calculate_summary()
        )

        self._manager.lockerChanged.connect(
            self._on_locker_changed
        )

        self._manager.lockerStructureAboutToChange.connect(
            self._begin_structure_reset
        )

        self._manager.lockerStructureChanged.connect(
            self._end_structure_reset
        )

    # =========================================================
    # MODEL SIZE
    # =========================================================

    def rowCount(self, parent=QModelIndex()):

        if parent.isValid():
            return 0

        return len(self._lockers)

    # =========================================================
    # DATA
    # =========================================================

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None

        row = index.row()

        if (
            row < 0
            or row >= len(self._lockers)
        ):
            return None

        locker = self._lockers[row]

        if role == self.LockerIdRole:
            return locker.locker_id

        if role == self.SlaveAddressRole:
            return locker.slave_address

        if role == self.ChannelRole:
            return locker.channel

        if role == self.ActualStateRole:
            return locker.actual_state.value

        if role == self.ExpectedStateRole:
            return locker.expected_state.value

        if role == self.FaultRole:
            return locker.fault.value

        if role == self.OccupancyStateRole:
            return locker.occupancy_state.value

        if role == self.AssignedToRole:
            return locker.assigned_to or ""

        if role == self.AssignedAtRole:
            return locker.assigned_at or ""

        return None

    # =========================================================
    # ROLE NAMES FOR QML
    # =========================================================

    def roleNames(self):

        return {
            self.LockerIdRole:
                b"lockerId",

            self.SlaveAddressRole:
                b"slaveAddress",

            self.ChannelRole:
                b"channel",

            self.ActualStateRole:
                b"actualState",

            self.ExpectedStateRole:
                b"expectedState",

            self.FaultRole:
                b"fault",

            self.OccupancyStateRole:
                b"occupancyState",

            self.AssignedToRole:
                b"assignedTo",

            self.AssignedAtRole:
                b"assignedAt",
        }

    # =========================================================
    # LIVE SUMMARY FOR QML
    # =========================================================

    def _calculate_summary(self):

        free_count = 0
        occupied_count = 0
        open_count = 0
        fault_count = 0
        unknown_count = 0

        for locker in self._lockers:

            occupancy_state = (
                locker.occupancy_state.value
            )

            actual_state = (
                locker.actual_state.value
            )

            fault = (
                locker.fault.value
            )

            # Occupancy is independent from the physical state.
            if occupancy_state == "occupied":
                occupied_count += 1
            else:
                free_count += 1

            # Physical/diagnostic counters intentionally overlap
            # with occupancy counters.
            if actual_state == "open":
                open_count += 1

            if fault != "none":
                fault_count += 1

            if actual_state == "unknown":
                unknown_count += 1

        return (
            free_count,
            occupied_count,
            open_count,
            fault_count,
            unknown_count,
        )

    @pyqtProperty(
        int,
        notify=summaryChanged
    )
    def totalCount(self):

        return len(
            self._lockers
        )

    @pyqtProperty(
        int,
        notify=summaryChanged
    )
    def freeCount(self):

        return self._summary_cache[0]

    @pyqtProperty(
        int,
        notify=summaryChanged
    )
    def occupiedCount(self):

        return self._summary_cache[1]

    @pyqtProperty(
        int,
        notify=summaryChanged
    )
    def openCount(self):

        return self._summary_cache[2]

    @pyqtProperty(
        int,
        notify=summaryChanged
    )
    def faultCount(self):

        return self._summary_cache[3]

    @pyqtProperty(
        int,
        notify=summaryChanged
    )
    def unknownCount(self):

        return self._summary_cache[4]

    def _update_summary(self):

        new_summary = (
            self._calculate_summary()
        )

        if (
            new_summary
            == self._summary_cache
        ):
            return

        self._summary_cache = (
            new_summary
        )

        self.summaryChanged.emit()

    # =========================================================
    # STRUCTURE RESET
    # =========================================================

    def _begin_structure_reset(self):

        self.beginResetModel()

    def _end_structure_reset(self):

        self._lockers = (
            self._manager.get_all_lockers()
        )

        self._summary_cache = (
            self._calculate_summary()
        )

        self.endResetModel()

        # totalCount and all summary properties use this notifier.
        self.summaryChanged.emit()

    # =========================================================
    # MANAGER UPDATE
    # =========================================================

    def _on_locker_changed(
        self,
        locker_id: int
    ):

        for row, locker in enumerate(
            self._lockers
        ):

            if (
                locker.locker_id
                != locker_id
            ):
                continue

            model_index = self.index(
                row,
                0
            )

            self.dataChanged.emit(
                model_index,
                model_index,
                [
                    self.ActualStateRole,
                    self.ExpectedStateRole,
                    self.FaultRole,
                    self.OccupancyStateRole,
                    self.AssignedToRole,
                    self.AssignedAtRole,
                ]
            )

            self._update_summary()

            return
