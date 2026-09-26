import socket
import time

from PyQt5.QtCore import (
    QCoreApplication,
)

from core.locker_manager import (
    LockerManager,
)

from storage.database import (
    LockerDatabase,
)

from network.kstp_service import (
    KstpApplicationService,
)

from network.protocol import (
    KstpStreamParser,
    MessageType,
    encode_frame,
)


# ============================================================
# TEST HELPERS
# ============================================================

def get_app():

    app = (
        QCoreApplication.instance()
    )

    if app is None:

        app = QCoreApplication(
            []
        )

    return app


class StubLockerController:

    def __init__(
        self,
        accept_open=True
    ):

        self.accept_open = (
            accept_open
        )

        self.open_calls = []

    def openLocker(
        self,
        locker_id
    ):

        self.open_calls.append(
            locker_id
        )

        return self.accept_open


def create_runtime(
    tmp_path,
    accept_open=True
):

    database = LockerDatabase(
        tmp_path
        / "kstp_service.db"
    )

    manager = LockerManager(
        database=database
    )

    for locker_id in range(
        1,
        4
    ):

        manager.add_locker(
            locker_id=locker_id,
            slave_address=1,
            channel=locker_id
        )

    controller = (
        StubLockerController(
            accept_open=accept_open
        )
    )

    service = KstpApplicationService(
        locker_manager=manager,
        locker_controller=controller,
        host="127.0.0.1",
        port=0
    )

    return (
        service,
        manager,
        controller,
        database
    )


def connect_client(
    service
):

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client.settimeout(
        2.0
    )

    client.connect(
        (
            "127.0.0.1",
            service.bound_port
        )
    )

    client.setblocking(
        False
    )

    return client


def receive_frame(
    app,
    client,
    timeout=2.0
):

    parser = KstpStreamParser()

    deadline = (
        time.monotonic()
        + timeout
    )

    while (
        time.monotonic()
        < deadline
    ):

        # Critical:
        # allows QtCommandBridge queued events to execute
        # on this test's Qt/main thread.
        app.processEvents()

        try:

            data = client.recv(
                4096
            )

        except BlockingIOError:

            data = None

        if data:

            frames = parser.feed(
                data
            )

            if frames:

                return frames[0]

        time.sleep(
            0.005
        )

    raise AssertionError(
        "Timed out waiting for KSTP response."
    )


# ============================================================
# ALLOCATE END-TO-END
# ============================================================

def test_allocate_round_trip_updates_database(
    tmp_path
):

    app = get_app()

    (
        service,
        manager,
        controller,
        database
    ) = create_runtime(
        tmp_path
    )

    service.start()

    client = connect_client(
        service
    )

    try:

        client.sendall(
            encode_frame(
                MessageType.ALLOCATE_LOCKER,
                1001,
                {
                    "locker_id": 2,
                    "person_id": "P10025",
                }
            )
        )

        response = receive_frame(
            app,
            client
        )

        assert (
            response.message_type
            == MessageType.RESPONSE_OK
        )

        assert (
            response.request_id
            == 1001
        )

        assert response.payload == {
            "result": "allocated",
            "locker_id": 2,
        }

        assert (
            manager.get_locker(
                2
            ).assigned_to
            == "P10025"
        )

        assignment = (
            database.get_assignment(
                2
            )
        )

        assert (
            assignment["assigned_to"]
            == "P10025"
        )

    finally:

        client.close()
        service.stop()
        database.close()


# ============================================================
# RELEASE END-TO-END
# ============================================================

def test_release_round_trip_updates_database(
    tmp_path
):

    app = get_app()

    (
        service,
        manager,
        controller,
        database
    ) = create_runtime(
        tmp_path
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    service.start()

    client = connect_client(
        service
    )

    try:

        client.sendall(
            encode_frame(
                MessageType.RELEASE_LOCKER,
                1002,
                {
                    "locker_id": 2,
                    "person_id": "P10025",
                }
            )
        )

        response = receive_frame(
            app,
            client
        )

        assert (
            response.message_type
            == MessageType.RESPONSE_OK
        )

        assert response.payload == {
            "result": "released",
            "locker_id": 2,
        }

        assert (
            database.get_assignment(
                2
            )
            is None
        )

        assert (
            manager.get_locker(
                2
            ).assigned_to
            is None
        )

    finally:

        client.close()
        service.stop()
        database.close()


# ============================================================
# OPEN WITH UNKNOWN HARDWARE STATE
# ============================================================

def test_open_unknown_state_is_rejected(
    tmp_path
):

    app = get_app()

    (
        service,
        manager,
        controller,
        database
    ) = create_runtime(
        tmp_path
    )

    service.start()

    client = connect_client(
        service
    )

    try:

        # No hardware feedback was provided.
        # Physical state therefore remains UNKNOWN.

        client.sendall(
            encode_frame(
                MessageType.OPEN_LOCKER,
                2001,
                {
                    "locker_id": 1
                }
            )
        )

        response = receive_frame(
            app,
            client
        )

        assert (
            response.message_type
            == MessageType.RESPONSE_ERROR
        )

        assert response.payload == {
            "error":
                "locker_state_unknown",
            "locker_id": 1,
        }

        # Controller must not be called when the physical
        # state is unknown.
        assert (
            controller.open_calls
            == []
        )

    finally:

        client.close()
        service.stop()
        database.close()


# ============================================================
# OPEN WITH VALID CLOSED HARDWARE STATE
# ============================================================

def test_open_closed_locker_is_sent_to_controller(
    tmp_path
):

    app = get_app()

    (
        service,
        manager,
        controller,
        database
    ) = create_runtime(
        tmp_path
    )

    # Simulate fresh real hardware feedback:
    # locker is physically closed and ready.
    manager.process_feedback(
        locker_id=1,
        is_open=False
    )

    service.start()

    client = connect_client(
        service
    )

    try:

        client.sendall(
            encode_frame(
                MessageType.OPEN_LOCKER,
                2002,
                {
                    "locker_id": 1
                }
            )
        )

        response = receive_frame(
            app,
            client
        )

        assert (
            controller.open_calls
            == [1]
        )

        assert (
            response.message_type
            == MessageType.RESPONSE_OK
        )

        assert response.payload == {
            "result": "open_requested",
            "locker_id": 1,
        }

    finally:

        client.close()
        service.stop()
        database.close()
