from __future__ import annotations

import socket
import threading

from typing import Callable, Optional, Tuple

from network.protocol import (
    KstpFrame,
    KstpStreamParser,
    MessageType,
    ProtocolError,
    encode_frame,
)


# ============================================================
# TCP SERVER CONSTANTS
# ============================================================

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5055

DEFAULT_RECV_SIZE = 4096
DEFAULT_ACCEPT_TIMEOUT = 0.25
DEFAULT_CLIENT_TIMEOUT = 0.50


# ============================================================
# TCP SERVER ERRORS
# ============================================================

class TcpServerError(Exception):
    pass


class ServerAlreadyRunningError(TcpServerError):
    pass


class NoClientConnectedError(TcpServerError):
    pass


class ClientRejectedError(TcpServerError):
    pass


# ============================================================
# CALLBACK TYPES
# ============================================================

FrameCallback = Callable[
    [KstpFrame],
    None
]

ClientCallback = Callable[
    [Tuple[str, int]],
    None
]

ErrorCallback = Callable[
    [Exception],
    None
]


# ============================================================
# KSTP TCP SERVER
# ============================================================

class KstpTcpServer:
    """
    Lightweight single-active-client TCP server for KSTP.

    Responsibilities:
        - listen for TCP connections
        - allow one active client
        - receive TCP bytes
        - feed bytes into KstpStreamParser
        - deliver complete KstpFrame objects
        - send KSTP frames to the active client

    Important:
        Callbacks execute from worker threads.

        They must not manipulate QML/Qt GUI objects directly.

        A Qt-safe bridge will be added later when the TCP layer
        is connected to LockerManager and the GUI.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        recv_size: int = DEFAULT_RECV_SIZE,
        on_frame: Optional[
            FrameCallback
        ] = None,
        on_client_connected: Optional[
            ClientCallback
        ] = None,
        on_client_disconnected: Optional[
            ClientCallback
        ] = None,
        on_error: Optional[
            ErrorCallback
        ] = None,
    ):

        self._host = str(host)
        self._port = int(port)
        self._recv_size = int(
            recv_size
        )

        if not (
            0 <= self._port <= 65535
        ):
            raise ValueError(
                "port must be between "
                "0 and 65535."
            )

        if self._recv_size <= 0:
            raise ValueError(
                "recv_size must be positive."
            )

        self._on_frame = on_frame

        self._on_client_connected = (
            on_client_connected
        )

        self._on_client_disconnected = (
            on_client_disconnected
        )

        self._on_error = on_error

        self._server_socket: Optional[
            socket.socket
        ] = None

        self._client_socket: Optional[
            socket.socket
        ] = None

        self._client_address: Optional[
            Tuple[str, int]
        ] = None

        self._server_thread: Optional[
            threading.Thread
        ] = None

        self._client_thread: Optional[
            threading.Thread
        ] = None

        self._stop_event = (
            threading.Event()
        )

        self._running_event = (
            threading.Event()
        )

        self._client_lock = (
            threading.Lock()
        )

        self._send_lock = (
            threading.Lock()
        )

        self._bound_host = self._host
        self._bound_port = self._port

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def host(self) -> str:

        return self._host

    @property
    def port(self) -> int:

        return self._port

    @property
    def bound_host(self) -> str:

        return self._bound_host

    @property
    def bound_port(self) -> int:

        return self._bound_port

    @property
    def is_running(self) -> bool:

        return (
            self._running_event.is_set()
        )

    @property
    def has_client(self) -> bool:

        with self._client_lock:

            return (
                self._client_socket
                is not None
            )

    @property
    def client_address(
        self
    ) -> Optional[Tuple[str, int]]:

        with self._client_lock:

            return self._client_address

    # ========================================================
    # START
    # ========================================================

    def start(self):

        if self.is_running:

            raise ServerAlreadyRunningError(
                "KSTP TCP server is "
                "already running."
            )

        self._stop_event.clear()

        server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        try:

            server_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            server_socket.bind(
                (
                    self._host,
                    self._port
                )
            )

            server_socket.listen(
                1
            )

            server_socket.settimeout(
                DEFAULT_ACCEPT_TIMEOUT
            )

            (
                self._bound_host,
                self._bound_port
            ) = server_socket.getsockname()

        except Exception:

            server_socket.close()
            raise

        self._server_socket = (
            server_socket
        )

        self._running_event.set()

        self._server_thread = (
            threading.Thread(
                target=self._accept_loop,
                name="KardanSoft-KSTP-Server",
                daemon=True
            )
        )

        self._server_thread.start()

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        self._stop_event.set()

        # ----------------------------------------------------
        # Stop active client connection.
        # ----------------------------------------------------

        with self._client_lock:

            client_socket = (
                self._client_socket
            )

        if client_socket is not None:

            self._close_socket(
                client_socket
            )

        # ----------------------------------------------------
        # Stop listening socket.
        # ----------------------------------------------------

        server_socket = (
            self._server_socket
        )

        if server_socket is not None:

            self._close_socket(
                server_socket
            )

        # ----------------------------------------------------
        # Wait briefly for worker threads.
        # ----------------------------------------------------

        current_thread = (
            threading.current_thread()
        )

        client_thread = (
            self._client_thread
        )

        if (
            client_thread is not None
            and client_thread.is_alive()
            and client_thread
            is not current_thread
        ):

            client_thread.join(
                timeout=2.0
            )

        server_thread = (
            self._server_thread
        )

        if (
            server_thread is not None
            and server_thread.is_alive()
            and server_thread
            is not current_thread
        ):

            server_thread.join(
                timeout=2.0
            )

        self._server_socket = None
        self._server_thread = None
        self._client_thread = None

        self._running_event.clear()

    # ========================================================
    # SEND
    # ========================================================

    def send_frame(
        self,
        message_type: MessageType,
        request_id: int,
        payload: dict
    ):

        raw = encode_frame(
            message_type,
            request_id,
            payload
        )

        with self._client_lock:

            client_socket = (
                self._client_socket
            )

        if client_socket is None:

            raise NoClientConnectedError(
                "No TCP client is connected."
            )

        try:

            with self._send_lock:

                client_socket.sendall(
                    raw
                )

        except OSError as exc:

            self._emit_error(
                exc
            )

            raise TcpServerError(
                "Failed to send KSTP frame."
            ) from exc

    # ========================================================
    # ACCEPT LOOP
    # ========================================================

    def _accept_loop(self):

        try:

            while not (
                self._stop_event.is_set()
            ):

                server_socket = (
                    self._server_socket
                )

                if server_socket is None:
                    break

                try:

                    (
                        client_socket,
                        client_address
                    ) = server_socket.accept()

                except socket.timeout:
                    continue

                except OSError as exc:

                    if (
                        self._stop_event.is_set()
                    ):
                        break

                    self._emit_error(
                        exc
                    )

                    continue

                # --------------------------------------------
                # Only one active client is allowed.
                # --------------------------------------------

                with self._client_lock:

                    client_exists = (
                        self._client_socket
                        is not None
                    )

                    if not client_exists:

                        self._client_socket = (
                            client_socket
                        )

                        self._client_address = (
                            client_address
                        )

                if client_exists:

                    self._close_socket(
                        client_socket
                    )

                    self._emit_error(
                        ClientRejectedError(
                            "A second TCP client "
                            "was rejected."
                        )
                    )

                    continue

                client_socket.settimeout(
                    DEFAULT_CLIENT_TIMEOUT
                )

                self._client_thread = (
                    threading.Thread(
                        target=self._client_loop,
                        args=(
                            client_socket,
                            client_address
                        ),
                        name=(
                            "KardanSoft-KSTP-Client"
                        ),
                        daemon=True
                    )
                )

                self._client_thread.start()

        finally:

            self._running_event.clear()

    # ========================================================
    # CLIENT LOOP
    # ========================================================

    def _client_loop(
        self,
        client_socket: socket.socket,
        client_address: Tuple[str, int]
    ):

        parser = KstpStreamParser()

        self._emit_client_connected(
            client_address
        )

        try:

            while not (
                self._stop_event.is_set()
            ):

                try:

                    data = client_socket.recv(
                        self._recv_size
                    )

                except socket.timeout:
                    continue

                except OSError as exc:

                    if not (
                        self._stop_event.is_set()
                    ):

                        self._emit_error(
                            exc
                        )

                    break

                if not data:
                    break

                try:

                    frames = parser.feed(
                        data
                    )

                except ProtocolError as exc:

                    self._emit_error(
                        exc
                    )

                    # Protocol corruption closes the
                    # connection. The next client must start
                    # with a clean stream parser.
                    break

                for frame in frames:

                    self._emit_frame(
                        frame
                    )

        finally:

            self._close_socket(
                client_socket
            )

            with self._client_lock:

                if (
                    self._client_socket
                    is client_socket
                ):

                    self._client_socket = None
                    self._client_address = None

            self._emit_client_disconnected(
                client_address
            )

    # ========================================================
    # CALLBACK HELPERS
    # ========================================================

    def _emit_frame(
        self,
        frame: KstpFrame
    ):

        callback = self._on_frame

        if callback is None:
            return

        try:

            callback(
                frame
            )

        except Exception as exc:

            self._emit_error(
                exc
            )

    def _emit_client_connected(
        self,
        address: Tuple[str, int]
    ):

        callback = (
            self._on_client_connected
        )

        if callback is None:
            return

        try:

            callback(
                address
            )

        except Exception as exc:

            self._emit_error(
                exc
            )

    def _emit_client_disconnected(
        self,
        address: Tuple[str, int]
    ):

        callback = (
            self._on_client_disconnected
        )

        if callback is None:
            return

        try:

            callback(
                address
            )

        except Exception as exc:

            self._emit_error(
                exc
            )

    def _emit_error(
        self,
        error: Exception
    ):

        callback = self._on_error

        if callback is None:
            return

        try:

            callback(
                error
            )

        except Exception:

            # An exception inside the error callback must
            # never kill the network worker.
            pass

    # ========================================================
    # SOCKET HELPER
    # ========================================================

    @staticmethod
    def _close_socket(
        sock: socket.socket
    ):

        try:

            sock.shutdown(
                socket.SHUT_RDWR
            )

        except OSError:
            pass

        try:

            sock.close()

        except OSError:
            pass

    # ========================================================
    # CONTEXT MANAGER
    # ========================================================

    def __enter__(self):

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        self.stop()

        return False
