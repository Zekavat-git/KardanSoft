import struct

import pytest

from network.protocol import (
    HEADER_SIZE,
    HEADER_STRUCT,
    MAGIC,
    MAX_PAYLOAD,
    VERSION,
    ExtraDataError,
    IncompleteFrameError,
    InvalidMagicError,
    InvalidPayloadError,
    InvalidRequestIdError,
    KstpStreamParser,
    MessageType,
    PayloadTooLargeError,
    UnsupportedVersionError,
    UnknownMessageTypeError,
    decode_frame,
    encode_frame,
)


def test_header_is_exactly_12_bytes():

    assert HEADER_SIZE == 12


def test_allocate_round_trip():

    raw = encode_frame(
        MessageType.ALLOCATE_LOCKER,
        1001,
        {
            "locker_id": 17,
            "person_id": "P10025",
        }
    )

    frame = decode_frame(
        raw
    )

    assert (
        frame.message_type
        == MessageType.ALLOCATE_LOCKER
    )

    assert frame.request_id == 1001

    assert frame.payload == {
        "locker_id": 17,
        "person_id": "P10025",
    }


def test_open_header_layout():

    raw = encode_frame(
        MessageType.OPEN_LOCKER,
        1002,
        {
            "locker_id": 17
        }
    )

    (
        magic,
        version,
        message_type,
        payload_length,
        request_id
    ) = HEADER_STRUCT.unpack(
        raw[:HEADER_SIZE]
    )

    assert magic == b"KS"
    assert version == 1
    assert message_type == 0x02
    assert request_id == 1002

    assert payload_length == (
        len(raw)
        - HEADER_SIZE
    )


def test_payload_is_compact_json():

    raw = encode_frame(
        MessageType.OPEN_LOCKER,
        1,
        {
            "locker_id": 17
        }
    )

    payload = raw[
        HEADER_SIZE:
    ]

    assert payload == (
        b'{"locker_id":17}'
    )


def test_unicode_payload_is_utf8():

    raw = encode_frame(
        MessageType.ALLOCATE_LOCKER,
        2,
        {
            "locker_id": 1,
            "person_id": "کاربر-۱۲۳",
        }
    )

    frame = decode_frame(
        raw
    )

    assert (
        frame.payload["person_id"]
        == "کاربر-۱۲۳"
    )


def test_parser_accepts_frame_byte_by_byte():

    raw = encode_frame(
        MessageType.OPEN_LOCKER,
        10,
        {
            "locker_id": 5
        }
    )

    parser = KstpStreamParser()

    frames = []

    for value in raw:

        frames.extend(
            parser.feed(
                bytes([value])
            )
        )

    assert len(frames) == 1

    assert (
        frames[0].message_type
        == MessageType.OPEN_LOCKER
    )

    assert frames[0].request_id == 10
    assert frames[0].payload["locker_id"] == 5
    assert parser.buffered_bytes == 0


def test_parser_handles_multiple_frames_together():

    first = encode_frame(
        MessageType.ALLOCATE_LOCKER,
        100,
        {
            "locker_id": 2,
            "person_id": "P1",
        }
    )

    second = encode_frame(
        MessageType.OPEN_LOCKER,
        101,
        {
            "locker_id": 2
        }
    )

    third = encode_frame(
        MessageType.RELEASE_LOCKER,
        102,
        {
            "locker_id": 2,
            "person_id": "P1",
        }
    )

    parser = KstpStreamParser()

    frames = parser.feed(
        first
        + second
        + third
    )

    assert len(frames) == 3

    assert [
        frame.request_id
        for frame in frames
    ] == [
        100,
        101,
        102,
    ]

    assert parser.buffered_bytes == 0


def test_parser_keeps_partial_frame():

    raw = encode_frame(
        MessageType.OPEN_LOCKER,
        50,
        {
            "locker_id": 7
        }
    )

    parser = KstpStreamParser()

    first_result = parser.feed(
        raw[:8]
    )

    assert first_result == []
    assert parser.buffered_bytes == 8

    second_result = parser.feed(
        raw[8:]
    )

    assert len(second_result) == 1
    assert parser.buffered_bytes == 0


def test_invalid_magic_is_rejected():

    raw = bytearray(
        encode_frame(
            MessageType.OPEN_LOCKER,
            1,
            {
                "locker_id": 1
            }
        )
    )

    raw[0:2] = b"XX"

    with pytest.raises(
        InvalidMagicError
    ):
        decode_frame(
            bytes(raw)
        )


def test_wrong_version_is_rejected():

    raw = bytearray(
        encode_frame(
            MessageType.OPEN_LOCKER,
            1,
            {
                "locker_id": 1
            }
        )
    )

    raw[2] = VERSION + 1

    with pytest.raises(
        UnsupportedVersionError
    ):
        decode_frame(
            bytes(raw)
        )


def test_unknown_message_type_is_rejected():

    payload = b'{"locker_id":1}'

    raw = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        0x55,
        len(payload),
        1
    ) + payload

    with pytest.raises(
        UnknownMessageTypeError
    ):
        decode_frame(
            raw
        )


def test_oversized_payload_is_rejected_on_encode():

    with pytest.raises(
        PayloadTooLargeError
    ):
        encode_frame(
            MessageType.RESPONSE_ERROR,
            1,
            {
                "message":
                    "X"
                    * (
                        MAX_PAYLOAD
                        + 100
                    )
            }
        )


def test_oversized_declared_payload_is_rejected():

    raw = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        int(
            MessageType.OPEN_LOCKER
        ),
        MAX_PAYLOAD + 1,
        1
    )

    with pytest.raises(
        PayloadTooLargeError
    ):
        decode_frame(
            raw
        )


def test_invalid_json_is_rejected():

    payload = b"{bad-json}"

    raw = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        int(
            MessageType.OPEN_LOCKER
        ),
        len(payload),
        1
    ) + payload

    with pytest.raises(
        InvalidPayloadError
    ):
        decode_frame(
            raw
        )


def test_non_object_json_is_rejected():

    payload = b"[1,2,3]"

    raw = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        int(
            MessageType.OPEN_LOCKER
        ),
        len(payload),
        1
    ) + payload

    with pytest.raises(
        InvalidPayloadError
    ):
        decode_frame(
            raw
        )


def test_invalid_request_id_is_rejected():

    with pytest.raises(
        InvalidRequestIdError
    ):
        encode_frame(
            MessageType.OPEN_LOCKER,
            -1,
            {
                "locker_id": 1
            }
        )

    with pytest.raises(
        InvalidRequestIdError
    ):
        encode_frame(
            MessageType.OPEN_LOCKER,
            0x100000000,
            {
                "locker_id": 1
            }
        )


def test_incomplete_frame_is_rejected():

    raw = encode_frame(
        MessageType.OPEN_LOCKER,
        1,
        {
            "locker_id": 1
        }
    )

    with pytest.raises(
        IncompleteFrameError
    ):
        decode_frame(
            raw[:-1]
        )


def test_extra_data_is_rejected_by_exact_decoder():

    raw = encode_frame(
        MessageType.OPEN_LOCKER,
        1,
        {
            "locker_id": 1
        }
    )

    with pytest.raises(
        ExtraDataError
    ):
        decode_frame(
            raw
            + b"extra"
        )


def test_allocate_reference_vector():

    raw = encode_frame(
        MessageType.ALLOCATE_LOCKER,
        1001,
        {
            "locker_id": 17,
            "person_id": "P10025",
        }
    )

    expected = bytes.fromhex(
        "4b 53 "
        "01 "
        "01 "
        "00 00 00 25 "
        "00 00 03 e9 "
        "7b 22 6c 6f 63 6b 65 72 5f 69 64 22 3a 31 37 "
        "2c 22 70 65 72 73 6f 6e 5f 69 64 22 3a 22 "
        "50 31 30 30 32 35 22 7d"
    )

    assert raw == expected
