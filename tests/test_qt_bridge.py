import threading
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

from network.command_handler import (
    CommandHandler,
    CommandResponse,
)

from network.protocol import (
    KstpFrame,
    MessageType,
)

from network.qt_bridge import (
    QtCommandBridge,
)


# ============================================================
# QT TEST HELPERS
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


def wait_until(
    app,
    predicate,
    timeout=2.0
):

    deadline = (
        time.monotonic()
        + timeout
    )

    while (
        time.monotonic()
        < deadline
    ):

        app.processEvents()

        if predicate():
            return True

        time.sleep(
            0.005
        )

    app.processEvents()

    return predicate()


# ============================================================
# TEST 1
# EXPLICIT THREAD HANDOFF
# ============================================================

def test_frame_processing_occurs_on_qt_thread():

    app = get_app()

    main_thread_id = (
        threading.get_ident()
    )

    class RecordingHandler:

        def __init__(self):

            self.thread_id = None

        def handle(
            self,
            frame
        ):

            self.thread_id = (
                threading.get_ident()
            )

            return CommandResponse(
                message_type=(
                    MessageType.RESPONSE_OK
                ),
                request_id=(
                    frame.request_id
                ),
                payload={
                    "result": "ok"
                }
            )

    handler = RecordingHandler()

    sent = []
    sender_threads = []

    def response_sender(
        message_type,
        request_id,
        payload
    ):

        sender_threads.append(
            threading.get_ident()
        )

        sent.append(
            (
                message_type,
                request_id,
                payload
            )
        )

    bridge = QtCommandBridge(
        command_handler=handler,
        response_sender=response_sender
    )

    frame = KstpFrame(
        message_type=(
            MessageType.OPEN_LOCKER
        ),
        request_id=1001,
        payload={
            "locker_id": 1
        }
    )

    worker_thread_id = []

    def worker():

        worker_thread_id.append(
            threading.get_ident()
        )

        bridge.submit_frame(
            frame
        )

    thread = threading.Thread(
        target=worker
    )

    thread.start()
    thread.join()

    assert wait_until(
        app,
        lambda:
        len(sent) == 1
    )

    assert (
        worker_thread_id[0]
        != main_thread_id
    )

    assert (
        handler.thread_id
        == main_thread_id
    )

    assert (
        sender_threads[0]
        == main_thread_id
    )


# ============================================================
# TEST 2
# SQLITE / LOCKER MANAGER SAFETY
# ============================================================

def test_allocate_from_worker_is_executed_safely_on_qt_thread(
    tmp_path
):

    app = get_app()

    database = LockerDatabase(
        tmp_path
        / "qt_bridge.db"
    )

    manager = LockerManager(
        database=database
    )

    manager.add_locker(
        locker_id=1,
        slave_address=1,
        channel=1
    )

    handler = CommandHandler(
        locker_manager=manager
    )

    sent = []

    def response_sender(
        message_type,
        request_id,
        payload
    ):

        sent.append(
            (
                message_type,
                request_id,
                payload
            )
        )

    bridge = QtCommandBridge(
        command_handler=handler,
        response_sender=response_sender
    )

    frame = KstpFrame(
        message_type=(
            MessageType.ALLOCATE_LOCKER
        ),
        request_id=2001,
        payload={
            "locker_id": 1,
            "person_id": "P10025",
        }
    )

    thread = threading.Thread(
        target=lambda:
        bridge.submit_frame(
            frame
        )
    )

    thread.start()
    thread.join()

    assert wait_until(
        app,
        lambda:
        len(sent) == 1
    )

    (
        message_type,
        request_id,
        payload
    ) = sent[0]

    assert (
        message_type
        == MessageType.RESPONSE_OK
    )

    assert request_id == 2001

    assert payload == {
        "result": "allocated",
        "locker_id": 1,
    }

    locker = manager.get_locker(
        1
    )

    assert (
        locker.assigned_to
        == "P10025"
    )

    assignment = (
        database.get_assignment(
            1
        )
    )

    assert (
        assignment["assigned_to"]
        == "P10025"
    )

    database.close()


# ============================================================
# TEST 3
# RELEASE THROUGH QUEUED BRIDGE
# ============================================================

def test_release_from_worker_updates_business_state(
    tmp_path
):

    app = get_app()

    database = LockerDatabase(
        tmp_path
        / "qt_release.db"
    )

    manager = LockerManager(
        database=database
    )

    manager.add_locker(
        locker_id=1,
        slave_address=1,
        channel=1
    )

    manager.allocate_to_person(
        1,
        "P10025"
    )

    handler = CommandHandler(
        locker_manager=manager
    )

    sent = []

    bridge = QtCommandBridge(
        command_handler=handler,
        response_sender=(
            lambda message_type,
                   request_id,
                   payload:
            sent.append(
                (
                    message_type,
                    request_id,
                    payload
                )
            )
        )
    )

    frame = KstpFrame(
        message_type=(
            MessageType.RELEASE_LOCKER
        ),
        request_id=2002,
        payload={
            "locker_id": 1,
            "person_id": "P10025",
        }
    )

    thread = threading.Thread(
        target=lambda:
        bridge.submit_frame(
            frame
        )
    )

    thread.start()
    thread.join()

    assert wait_until(
        app,
        lambda:
        len(sent) == 1
    )

    assert sent[0] == (
        MessageType.RESPONSE_OK,
        2002,
        {
            "result": "released",
            "locker_id": 1,
        }
    )

    locker = manager.get_locker(
        1
    )

    assert (
        locker.assigned_to
        is None
    )

    assert (
        database.get_assignment(
            1
        )
        is None
    )

    database.close()


# ============================================================
# TEST 4
# OPEN CALLBACK THROUGH QT THREAD
# ============================================================

def test_open_callback_runs_on_qt_thread(
    tmp_path
):

    app = get_app()

    main_thread_id = (
        threading.get_ident()
    )

    database = LockerDatabase(
        tmp_path
        / "qt_open.db"
    )

    manager = LockerManager(
        database=database
    )

    manager.add_locker(
        locker_id=1,
        slave_address=1,
        channel=1
    )

    open_calls = []

    def open_handler(
        locker_id
    ):

        open_calls.append(
            (
                locker_id,
                threading.get_ident()
            )
        )

        return (
            True,
            "open_requested"
        )

    handler = CommandHandler(
        locker_manager=manager,
        open_handler=open_handler
    )

    sent = []

    bridge = QtCommandBridge(
        command_handler=handler,
        response_sender=(
            lambda message_type,
                   request_id,
                   payload:
            sent.append(
                (
                    message_type,
                    request_id,
                    payload
                )
            )
        )
    )

    frame = KstpFrame(
        message_type=(
            MessageType.OPEN_LOCKER
        ),
        request_id=3001,
        payload={
            "locker_id": 1
        }
    )

    thread = threading.Thread(
        target=lambda:
        bridge.submit_frame(
            frame
        )
    )

    thread.start()
    thread.join()

    assert wait_until(
        app,
        lambda:
        len(sent) == 1
    )

    assert open_calls == [
        (
            1,
            main_thread_id
        )
    ]

    assert sent[0] == (
        MessageType.RESPONSE_OK,
        3001,
        {
            "result":
                "open_requested",
            "locker_id": 1,
        }
    )

    database.close()


# ============================================================
# TEST 5
# RESPONSE SEND ERROR IS CONTAINED
# ============================================================

def test_response_send_error_does_not_escape_qt_slot():

    app = get_app()

    class Handler:

        def handle(
            self,
            frame
        ):

            return CommandResponse(
                message_type=(
                    MessageType.RESPONSE_OK
                ),
                request_id=(
                    frame.request_id
                ),
                payload={
                    "result": "ok"
                }
            )

    errors = []

    def failing_sender(
        message_type,
        request_id,
        payload
    ):

        raise RuntimeError(
            "simulated send failure"
        )

    bridge = QtCommandBridge(
        command_handler=Handler(),
        response_sender=failing_sender
    )

    bridge.errorOccurred.connect(
        errors.append
    )

    frame = KstpFrame(
        message_type=(
            MessageType.OPEN_LOCKER
        ),
        request_id=4001,
        payload={
            "locker_id": 1
        }
    )

    thread = threading.Thread(
        target=lambda:
        bridge.submit_frame(
            frame
        )
    )

    thread.start()
    thread.join()

    assert wait_until(
        app,
        lambda:
        len(errors) == 1
    )

    assert (
        errors[0].startswith(
            "response_send_error:"
        )
    )

    assert (
        "simulated send failure"
        in errors[0]
    )
