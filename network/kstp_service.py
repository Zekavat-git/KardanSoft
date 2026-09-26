from __future__ import annotations

from PyQt5.QtCore import (
    QObject,
    Qt,
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
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

    # QML-visible connection state notifier.
    clientActiveChanged = pyqtSignal()

    # Emitted only after an OPEN request has been accepted.
    # Main.qml uses this to display the locker number.
    lockerOpenDisplayRequested = pyqtSignal(
        int,
        arguments=["lockerId"]
    )

    # TCP callbacks originate from worker threads.
    # This private signal transfers connection-state changes
    # safely onto the Qt main thread.
    _clientStateRequested = pyqtSignal(
        bool,
        str,
        int
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

        self._client_active = False
        self._active_client_host = ""
        self._active_client_port = 0

        self._clientStateRequested.connect(
            self._apply_client_state,
            Qt.QueuedConnection
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

    @pyqtProperty(
        bool,
        notify=clientActiveChanged
    )
    def clientActive(self):

        return self._client_active


    @pyqtSlot(
        bool,
        str,
        int
    )
    def _apply_client_state(
        self,
        connected: bool,
        host: str,
        port: int
    ):

        connected = bool(
            connected
        )

        host = str(
            host
        )

        port = int(
            port
        )

        if connected:

            state_changed = (
                not self._client_active
            )

            self._client_active = True
            self._active_client_host = host
            self._active_client_port = port

            if state_changed:
                self.clientActiveChanged.emit()

            print(
                "KSTP | GUI STATE | CONNECTED"
            )

            return


        # Ignore a stale disconnect belonging to an older
        # connection if a newer client is already active.
        if (
            self._client_active
            and
            (
                self._active_client_host != host
                or
                self._active_client_port != port
            )
        ):
            return


        state_changed = (
            self._client_active
        )

        self._client_active = False
        self._active_client_host = ""
        self._active_client_port = 0

        if state_changed:
            self.clientActiveChanged.emit()

        print(
            "KSTP | GUI STATE | DISCONNECTED"
        )


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

        # UNKNOWN is intentionally allowed here.
        # An explicit OPEN request must still be delivered to
        # the locker command path before fresh feedback exists.

        accepted = (
            self._locker_controller
            .openLocker(
                locker_id
            )
        )

        if accepted:

            self.lockerOpenDisplayRequested.emit(
                int(locker_id)
            )

            print(
                "KSTP | OPEN DISPLAY | "
                f"Locker={int(locker_id)}"
            )

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

        self._clientStateRequested.emit(
            True,
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

        self._clientStateRequested.emit(
            False,
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
