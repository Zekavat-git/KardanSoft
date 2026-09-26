from storage.database import LockerDatabase
from core.locker_manager import LockerManager


def create_manager(tmp_path):

    db_path = (
        tmp_path
        / "kardansoft_test.db"
    )

    database = LockerDatabase(
        db_path
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

    return (
        manager,
        database
    )


def test_allocate_locker(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    result = (
        manager.allocate_to_person(
            2,
            "P10025"
        )
    )

    assert result == (
        True,
        "allocated"
    )

    locker = manager.get_locker(
        2
    )

    assert (
        locker.occupancy_state.value
        == "occupied"
    )

    assert (
        locker.assigned_to
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

    database.close()


def test_repeat_same_allocation_is_idempotent(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    result = (
        manager.allocate_to_person(
            2,
            "P10025"
        )
    )

    assert result == (
        True,
        "already_allocated"
    )

    database.close()


def test_person_cannot_have_two_lockers(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    result = (
        manager.allocate_to_person(
            3,
            "P10025"
        )
    )

    assert result == (
        False,
        "person_already_allocated"
    )

    database.close()


def test_occupied_locker_rejects_other_person(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    result = (
        manager.allocate_to_person(
            2,
            "P99999"
        )
    )

    assert result == (
        False,
        "locker_already_allocated"
    )

    database.close()


def test_wrong_person_cannot_release_locker(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    result = (
        manager.release_from_person(
            2,
            "P99999"
        )
    )

    assert result == (
        False,
        "assignment_mismatch"
    )

    assert (
        database.get_assignment(
            2
        )
        is not None
    )

    database.close()


def test_correct_person_can_release_locker(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    manager.allocate_to_person(
        2,
        "P10025"
    )

    result = (
        manager.release_from_person(
            2,
            "P10025"
        )
    )

    assert result == (
        True,
        "released"
    )

    assert (
        database.get_assignment(
            2
        )
        is None
    )

    locker = manager.get_locker(
        2
    )

    assert (
        locker.occupancy_state.value
        == "free"
    )

    assert (
        locker.assigned_to
        is None
    )

    database.close()


def test_repeat_release_is_idempotent(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    result = (
        manager.release_from_person(
            2,
            "P10025"
        )
    )

    assert result == (
        True,
        "already_free"
    )

    database.close()


def test_invalid_locker_is_rejected(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    result = (
        manager.allocate_to_person(
            99,
            "P10025"
        )
    )

    assert result == (
        False,
        "locker_not_found"
    )

    database.close()


def test_empty_person_id_is_rejected(
    tmp_path
):

    manager, database = (
        create_manager(
            tmp_path
        )
    )

    result = (
        manager.allocate_to_person(
            2,
            "   "
        )
    )

    assert result == (
        False,
        "invalid_person_id"
    )

    database.close()
