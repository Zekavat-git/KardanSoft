from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
    pyqtProperty,
    QTimer,
)

from core.locker import (
    LockerState,
    ExpectedState,
    LockerFault,
)

from core.locker_manager import (
    LockerManager,
)


class LockerController(QObject):

    # =========================================================
    # SIGNALS
    # =========================================================

    statusChanged = pyqtSignal(str)

    # locker_id, actual_state, fault
    lockerStateChanged = pyqtSignal(
        int,
        str,
        str
    )

    batchBusyChanged = pyqtSignal()

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        manager: LockerManager
    ):

        super().__init__()

        self.manager = manager

        # Time allowed for OPEN feedback
        self.open_timeout_ms = 2000

        # Small delay between queued lockers
        self.next_locker_delay_ms = 500

        # Multi-locker queue
        self._open_queue = []

        self._active_locker_id = None

        self._batch_busy = False

        # -----------------------------------------------------
        # Manager signals
        # -----------------------------------------------------

        self.manager.lockerChanged.connect(
            self._on_locker_changed
        )

        self.manager.lockerFaultDetected.connect(
            self._on_fault_detected
        )

        self.manager.commandRejected.connect(
            self._on_command_rejected
        )

    # =========================================================
    # BATCH BUSY PROPERTY
    # =========================================================

    @pyqtProperty(
        bool,
        notify=batchBusyChanged
    )
    def batchBusy(self):

        return self._batch_busy

    def _set_batch_busy(
        self,
        value: bool
    ):

        if self._batch_busy == value:
            return

        self._batch_busy = value

        self.batchBusyChanged.emit()

    # =========================================================
    # CHECK LOCKER READY
    # =========================================================

    def _locker_ready_for_open(
        self,
        locker
    ):

        return (
            locker.actual_state
            == LockerState.CLOSED

            and

            locker.expected_state
            == ExpectedState.CLOSED

            and

            locker.fault
            == LockerFault.NONE
        )

    # =========================================================
    # OPEN SINGLE LOCKER
    # =========================================================

    @pyqtSlot(
        int,
        result=bool
    )
    def openLocker(
        self,
        locker_id: int
    ):

        count = self._enqueue_lockers(
            [locker_id]
        )

        return count > 0

    # =========================================================
    # OPEN MULTIPLE LOCKERS
    # =========================================================

    @pyqtSlot(
        "QVariantList",
        result=int
    )
    def openLockers(
        self,
        locker_ids
    ):

        return self._enqueue_lockers(
            locker_ids
        )

    # =========================================================
    # ADD LOCKERS TO QUEUE
    # =========================================================

    def _enqueue_lockers(
        self,
        locker_ids
    ):

        accepted = []

        seen = set()

        for value in locker_ids:

            try:
                locker_id = int(value)

            except (
                TypeError,
                ValueError
            ):
                continue

            if locker_id in seen:
                continue

            seen.add(locker_id)

            locker = (
                self.manager.get_locker(
                    locker_id
                )
            )

            if locker is None:
                continue

            if not self._locker_ready_for_open(
                locker
            ):
                continue

            # Don't add duplicate queue item
            if locker_id in self._open_queue:
                continue

            if (
                self._active_locker_id
                == locker_id
            ):
                continue

            accepted.append(
                locker_id
            )

        if not accepted:

            self.statusChanged.emit(
                "هیچ کمد آماده‌ای برای باز شدن انتخاب نشده است"
            )

            return 0

        self._open_queue.extend(
            accepted
        )

        self.statusChanged.emit(
            f"{len(accepted)} کمد در صف باز شدن قرار گرفت"
        )

        if not self._batch_busy:

            self._set_batch_busy(
                True
            )

            QTimer.singleShot(
                0,
                self._start_next_locker
            )

        return len(accepted)

    # =========================================================
    # START NEXT LOCKER
    # =========================================================

    def _start_next_locker(self):

        # Currently waiting for another locker
        if self._active_locker_id is not None:
            return

        # Queue finished
        if not self._open_queue:

            self._set_batch_busy(
                False
            )

            self.statusChanged.emit(
                "عملیات باز کردن کمدهای انتخاب‌شده پایان یافت"
            )

            return

        locker_id = (
            self._open_queue.pop(0)
        )

        locker = (
            self.manager.get_locker(
                locker_id
            )
        )

        # State may have changed while waiting
        if (
            locker is None
            or
            not self._locker_ready_for_open(
                locker
            )
        ):

            QTimer.singleShot(
                0,
                self._start_next_locker
            )

            return

        # Mark as active before sending command
        self._active_locker_id = (
            locker_id
        )

        result = (
            self.manager.request_open(
                locker_id
            )
        )

        if not result:

            self._active_locker_id = None

            QTimer.singleShot(
                0,
                self._start_next_locker
            )

            return

        self.statusChanged.emit(
            f"فرمان باز شدن کمد {locker_id} ارسال شد"
        )

        # Automatic OPEN timeout
        QTimer.singleShot(
            self.open_timeout_ms,
            lambda locker_id=locker_id:
            self._check_open_timeout(
                locker_id
            )
        )

    # =========================================================
    # OPEN TIMEOUT
    # =========================================================

    def _check_open_timeout(
        self,
        locker_id: int
    ):

        self.manager.open_timeout(
            locker_id
        )

    # =========================================================
    # COMPLETE CURRENT QUEUE ITEM
    # =========================================================

    def _complete_active_locker(
        self,
        locker_id: int
    ):

        if (
            self._active_locker_id
            != locker_id
        ):
            return

        self._active_locker_id = None

        QTimer.singleShot(
            self.next_locker_delay_ms,
            self._start_next_locker
        )

    # =========================================================
    # GET LOCKER STATE
    # =========================================================

    @pyqtSlot(
        int,
        result=str
    )
    def getLockerState(
        self,
        locker_id: int
    ):

        locker = (
            self.manager.get_locker(
                locker_id
            )
        )

        if locker is None:
            return "not_found"

        return locker.actual_state.value

    # =========================================================
    # GET LOCKER FAULT
    # =========================================================

    @pyqtSlot(
        int,
        result=str
    )
    def getLockerFault(
        self,
        locker_id: int
    ):

        locker = (
            self.manager.get_locker(
                locker_id
            )
        )

        if locker is None:
            return "not_found"

        return locker.fault.value

    # =========================================================
    # LOCKER CHANGED
    # =========================================================

    def _on_locker_changed(
        self,
        locker_id: int
    ):

        locker = (
            self.manager.get_locker(
                locker_id
            )
        )

        if locker is None:
            return

        self.lockerStateChanged.emit(
            locker_id,
            locker.actual_state.value,
            locker.fault.value
        )

        # -----------------------------------------------------
        # Successfully opened
        # -----------------------------------------------------

        if (
            locker.actual_state
            == LockerState.OPEN
        ):

            self.statusChanged.emit(
                f"کمد {locker_id} باز شد"
            )

            if (
                self._active_locker_id
                == locker_id
            ):

                QTimer.singleShot(
                    self.next_locker_delay_ms,
                    lambda locker_id=locker_id:
                    self._complete_active_locker(
                        locker_id
                    )
                )

        # -----------------------------------------------------
        # Normal closed status
        # -----------------------------------------------------

        elif (
            locker.actual_state
            == LockerState.CLOSED

            and

            locker.fault
            == LockerFault.NONE

            and

            locker.expected_state
            == ExpectedState.CLOSED
        ):

            self.statusChanged.emit(
                f"کمد {locker_id} بسته است"
            )

    # =========================================================
    # FAULT
    # =========================================================

    def _on_fault_detected(
        self,
        locker_id: int,
        fault: str
    ):

        if (
            fault
            == LockerFault.UNEXPECTED_OPEN.value
        ):

            message = (
                f"هشدار: کمد {locker_id} "
                f"بدون فرمان باز شده است"
            )

        elif (
            fault
            == LockerFault.FAILED_TO_OPEN.value
        ):

            message = (
                f"خطا: کمد {locker_id} "
                f"پس از فرمان باز نشد"
            )

        else:

            message = (
                f"خطا در کمد "
                f"{locker_id}: {fault}"
            )

        self.statusChanged.emit(
            message
        )

        # Failed current locker:
        # continue queue with next locker.
        if (
            fault
            == LockerFault.FAILED_TO_OPEN.value

            and

            self._active_locker_id
            == locker_id
        ):

            self._complete_active_locker(
                locker_id
            )

    # =========================================================
    # COMMAND REJECTED
    # =========================================================

    def _on_command_rejected(
        self,
        locker_id: int,
        reason: str
    ):

        if reason == "locker_not_found":

            message = (
                f"کمد شماره {locker_id} "
                f"وجود ندارد"
            )

        elif reason == "locker_already_open":

            message = (
                f"کمد شماره {locker_id} "
                f"از قبل باز است"
            )

        else:

            message = (
                f"فرمان کمد {locker_id} "
                f"رد شد: {reason}"
            )

        self.statusChanged.emit(
            message
        )