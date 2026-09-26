from __future__ import annotations

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)

from core.locker import (
    ExpectedState,
    LockerFault,
    LockerState,
)

from network.command_handler import (
    CommandHandler,
)

from network.qt_bridge import (
    QtCommandBridge,
)

from network.tcp_server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    KstpTcpServer,
)


class KstpApplicationService(QObject):
    """
    Composition layer for the complete KSTP server stack.

    TCP worker thread:
        KstpTcpServer

    Qt main thread:
        QtCommandBridge
        CommandHandler
        LockerManager
        LockerController
        SQLite / model updates

    This class intentionally does not know anything about QML.
    """

    clientConnected = pyqtSignal(
        str,
        int
    )

    clientDisconnected = pyqtSignal(
        str,
        int
    )

    networkError = pyqtSignal(
        str
    )

    def __init__(
        self,
        locker_manager,
        locker_controller,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        parent=None
    ):

        super().__init__(
            parent
        )

        if locker_manager is None:

            raise ValueError(
                "locker_manager is required."
            )

        if locker_controller is None:

            raise ValueError(
                "locker_controller is required."
            )

        self._locker_manager = (
            locker_manager
        )

        self._locker_controller = (
            locker_controller
        )

        # ----------------------------------------------------
        # BUSINESS COMMAND HANDLER
        # ----------------------------------------------------

        self._command_handler = (
            CommandHandler(
                locker_manager=(
                    self._locker_manager
                ),
                open_handler=(
                    self._handle_open_request
                )
            )
        )

        # ----------------------------------------------------
        # QT THREAD BRIDGE
        # ----------------------------------------------------

        self._bridge = QtCommandBridge(
            command_handler=(
                self._command_handler
            ),
            response_sender=(
                self._send_response
            ),
            parent=self
        )

        self._bridge.errorOccurred.connect(
            self._on_bridge_error
        )

        # ----------------------------------------------------
        # TCP SERVER
        # ----------------------------------------------------

        self._server = KstpTcpServer(
            host=host,
            port=port,
            on_frame=(
                self._bridge.submit_frame
            ),
            on_client_connected=(
                self._on_client_connected
            ),
            on_client_disconnected=(
                self._on_client_disconnected
            ),
            on_error=(
                self._on_tcp_error
            )
        )

    # ========================================================
    # PUBLIC STATE
    # ========================================================

    @property
    def is_running(self) -> bool:

        return (
            self._server.is_running
        )

    @property
    def bound_host(self) -> str:

        return (
            self._server.bound_host
        )

    @property
    def bound_port(self) -> int:

        return (
            self._server.bound_port
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def start(self):

        self._server.start()

        print(
            "KSTP | SERVER | STARTED | "
            f"{self.bound_host}:"
            f"{self.bound_port}"
        )

    def stop(self):

        if not self._server.is_running:
            return

        self._server.stop()

        print(
            "KSTP | SERVER | STOPPED"
        )

    # ========================================================
    # OPEN COMMAND
    # ========================================================

    def _handle_open_request(
        self,
        locker_id: int
    ):

        locker = (
            self._locker_manager
            .get_locker(
                locker_id
            )
        )

        if locker is None:

            return (
                False,
                "locker_not_found"
            )

        # A known hardware fault takes priority.
        if (
            locker.fault
            != LockerFault.NONE
        ):

            return (
                False,
                "locker_fault"
            )

        # Production NanoPi starts physical state as UNKNOWN
        # until fresh hardware feedback is received.
        if (
            locker.actual_state
            == LockerState.UNKNOWN
        ):

            return (
                False,
                "locker_state_unknown"
            )

        if (
            locker.actual_state
            == LockerState.OPEN
        ):

            return (
                False,
                "already_open"
            )

        if (
            locker.expected_state
            == ExpectedState.OPEN
        ):

            return (
                False,
                "open_already_pending"
            )

        accepted = (
            self._locker_controller
            .openLocker(
                locker_id
            )
        )

        if accepted:

            return (
                True,
                "open_requested"
            )

        # At this point the locker passed the public-state
        # checks above. A rejection normally means the
        # controller already has it queued/active or otherwise
        # declined to enqueue it.
        return (
            False,
            "open_request_rejected"
        )

    # ========================================================
    # RESPONSE PATH
    # ========================================================

    def _send_response(
        self,
        message_type,
        request_id: int,
        payload: dict
    ):

        self._server.send_frame(
            message_type,
            request_id,
            payload
        )

    # ========================================================
    # TCP CALLBACKS
    #
    # These callbacks originate in Python socket worker
    # threads. They must not touch LockerManager/QML.
    # Emitting Qt signals here is safe.
    # ========================================================

    def _on_client_connected(
        self,
        address
    ):

        host = str(
            address[0]
        )

        port = int(
            address[1]
        )

        print(
            "KSTP | CLIENT | CONNECTED | "
            f"{host}:{port}"
        )

        self.clientConnected.emit(
            host,
            port
        )

    def _on_client_disconnected(
        self,
        address
    ):

        host = str(
            address[0]
        )

        port = int(
            address[1]
        )

        print(
            "KSTP | CLIENT | DISCONNECTED | "
            f"{host}:{port}"
        )

        self.clientDisconnected.emit(
            host,
            port
        )

    def _on_tcp_error(
        self,
        error: Exception
    ):

        message = (
            f"tcp_error:"
            f"{type(error).__name__}:"
            f"{error}"
        )

        print(
            f"KSTP | ERROR | {message}"
        )

        self.networkError.emit(
            message
        )

    def _on_bridge_error(
        self,
        message: str
    ):

        print(
            f"KSTP | ERROR | {message}"
        )

        self.networkError.emit(
            message
        )
