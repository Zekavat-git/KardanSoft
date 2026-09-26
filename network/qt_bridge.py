from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import (
    QObject,
    Qt,
    pyqtSignal,
    pyqtSlot,
)

from network.command_handler import (
    CommandResponse,
)


ResponseSender = Callable[
    [
        object,
        int,
        dict
    ],
    None
]


class QtCommandBridge(QObject):
    """
    Thread-safe bridge between the TCP worker thread and
    the Qt application/main thread.

    Incoming KSTP frames may arrive from a Python socket
    worker thread.

    They are transferred to this QObject through an explicit
    Qt.QueuedConnection before CommandHandler is called.

    This protects:
        - LockerManager QObject access
        - SQLite thread affinity
        - QML/model updates
        - future LockerController operations
    """

    frameReceived = pyqtSignal(
        object
    )

    responseReady = pyqtSignal(
        object
    )

    errorOccurred = pyqtSignal(
        str
    )

    def __init__(
        self,
        command_handler,
        response_sender: ResponseSender,
        parent=None
    ):

        super().__init__(
            parent
        )

        if command_handler is None:

            raise ValueError(
                "command_handler is required."
            )

        if not callable(
            response_sender
        ):

            raise ValueError(
                "response_sender must be callable."
            )

        self._command_handler = (
            command_handler
        )

        self._response_sender = (
            response_sender
        )

        # Explicit QueuedConnection is intentional.
        #
        # Even when submit_frame() is called from the TCP
        # worker thread, _process_frame() executes in this
        # QObject's owning Qt thread.
        self.frameReceived.connect(
            self._process_frame,
            Qt.QueuedConnection
        )

    # ========================================================
    # TCP THREAD ENTRY POINT
    # ========================================================

    def submit_frame(
        self,
        frame
    ):

        """
        Safe to call from the TCP worker thread.
        """

        self.frameReceived.emit(
            frame
        )

    # ========================================================
    # QT MAIN THREAD PROCESSING
    # ========================================================

    @pyqtSlot(
        object
    )
    def _process_frame(
        self,
        frame
    ):

        try:

            response = (
                self._command_handler.handle(
                    frame
                )
            )

        except Exception as exc:

            self.errorOccurred.emit(
                "command_handler_error:"
                f"{type(exc).__name__}:"
                f"{exc}"
            )

            return

        if not isinstance(
            response,
            CommandResponse
        ):

            self.errorOccurred.emit(
                "command_handler_error:"
                "invalid_response_type"
            )

            return

        try:

            self._response_sender(
                response.message_type,
                response.request_id,
                response.payload
            )

        except Exception as exc:

            self.errorOccurred.emit(
                "response_send_error:"
                f"{type(exc).__name__}:"
                f"{exc}"
            )

            return

        self.responseReady.emit(
            response
        )
