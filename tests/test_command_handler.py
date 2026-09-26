from core.locker_manager import LockerManager
from storage.database import LockerDatabase

from network.command_handler import (
    CommandHandler,
)

from network.protocol import (
    KstpFrame,
    MessageType,
)


def create_handler(
    tmp_path,
    open_handler=None
):

    database = LockerDatabase(
        tmp_path
        / "command_handler.db"
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

    handler = CommandHandler(
        locker_manager=manager,
        open_handler=open_handler
    )

    return (
        handler,
        manager,
        database
    )


def make_frame(
    message_type,
    request_id,
    payload
):

    return KstpFrame(
        message_type=message_type,
        request_id=request_id,
        payload=payload
    )


def test_allocate_success(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.ALLOCATE_LOCKER,
            1001,
            {
                "locker_id": 2,
                "person_id": "P10025",
            }
        )
    )

    assert (
        response.message_type
        == MessageType.RESPONSE_OK
    )

    assert response.request_id == 1001

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

    database.close()


def test_allocate_conflict(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P1"
    )

    response = handler.handle(
        make_frame(
            MessageType.ALLOCATE_LOCKER,
            1002,
            {
                "locker_id": 2,
                "person_id": "P2",
            }
        )
    )

    assert (
        response.message_type
        == MessageType.RESPONSE_ERROR
    )

    assert response.payload == {
        "error":
            "locker_already_allocated",
        "locker_id": 2,
    }

    database.close()


def test_release_success(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    response = handler.handle(
        make_frame(
            MessageType.RELEASE_LOCKER,
            1003,
            {
                "locker_id": 2,
                "person_id": "P10025",
            }
        )
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
        manager.get_locker(
            2
        ).assigned_to
        is None
    )

    database.close()


def test_release_wrong_person(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P1"
    )

    response = handler.handle(
        make_frame(
            MessageType.RELEASE_LOCKER,
            1004,
            {
                "locker_id": 2,
                "person_id": "P2",
            }
        )
    )

    assert (
        response.message_type
        == MessageType.RESPONSE_ERROR
    )

    assert response.payload == {
        "error": "assignment_mismatch",
        "locker_id": 2,
    }

    database.close()


def test_open_success(
    tmp_path
):

    opened = []

    def open_handler(
        locker_id
    ):

        opened.append(
            locker_id
        )

        return (
            True,
            "open_requested"
        )

    handler, manager, database = (
        create_handler(
            tmp_path,
            open_handler
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.OPEN_LOCKER,
            2001,
            {
                "locker_id": 3
            }
        )
    )

    assert opened == [3]

    assert (
        response.message_type
        == MessageType.RESPONSE_OK
    )

    assert response.payload == {
        "result": "open_requested",
        "locker_id": 3,
    }

    database.close()


def test_open_rejected(
    tmp_path
):

    def open_handler(
        locker_id
    ):

        return (
            False,
            "already_open"
        )

    handler, manager, database = (
        create_handler(
            tmp_path,
            open_handler
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.OPEN_LOCKER,
            2002,
            {
                "locker_id": 1
            }
        )
    )

    assert (
        response.message_type
        == MessageType.RESPONSE_ERROR
    )

    assert response.payload == {
        "error": "already_open",
        "locker_id": 1,
    }

    database.close()


def test_open_without_handler(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.OPEN_LOCKER,
            2003,
            {
                "locker_id": 1
            }
        )
    )

    assert (
        response.message_type
        == MessageType.RESPONSE_ERROR
    )

    assert response.payload == {
        "error":
            "open_handler_unavailable",
        "locker_id": 1,
    }

    database.close()


def test_invalid_locker_id(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.ALLOCATE_LOCKER,
            3001,
            {
                "locker_id": "2",
                "person_id": "P1",
            }
        )
    )

    assert response.payload == {
        "error": "invalid_locker_id"
    }

    database.close()


def test_boolean_locker_id_rejected(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.OPEN_LOCKER,
            3002,
            {
                "locker_id": True
            }
        )
    )

    assert response.payload == {
        "error": "invalid_locker_id"
    }

    database.close()


def test_invalid_person_id(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.ALLOCATE_LOCKER,
            3003,
            {
                "locker_id": 1,
                "person_id": "   ",
            }
        )
    )

    assert response.payload == {
        "error": "invalid_person_id",
        "locker_id": 1,
    }

    database.close()


def test_non_string_person_id_rejected(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.ALLOCATE_LOCKER,
            3004,
            {
                "locker_id": 1,
                "person_id": 12345,
            }
        )
    )

    assert response.payload == {
        "error": "invalid_person_id",
        "locker_id": 1,
    }

    database.close()


def test_response_frame_is_not_accepted_as_request(
    tmp_path
):

    handler, manager, database = (
        create_handler(
            tmp_path
        )
    )

    response = handler.handle(
        make_frame(
            MessageType.RESPONSE_OK,
            4001,
            {
                "result": "anything"
            }
        )
    )

    assert (
        response.message_type
        == MessageType.RESPONSE_ERROR
    )

    assert response.payload == {
        "error":
            "unsupported_request_type"
    }

    assert response.request_id == 4001

    database.close()
