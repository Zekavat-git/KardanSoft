from __future__ import annotations

import json
import struct

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List


# ============================================================
# KSTP v1.0 CONSTANTS
# ============================================================

MAGIC = b"KS"
VERSION = 1

HEADER_STRUCT = struct.Struct(
    "!2sBBII"
)

HEADER_SIZE = HEADER_STRUCT.size

MAX_PAYLOAD = 2048
MAX_REQUEST_ID = 0xFFFFFFFF


# ============================================================
# MESSAGE TYPES
# ============================================================

class MessageType(IntEnum):

    ALLOCATE_LOCKER = 0x01
    OPEN_LOCKER = 0x02
    RELEASE_LOCKER = 0x03

    RESPONSE_OK = 0x80
    RESPONSE_ERROR = 0x81


# ============================================================
# PROTOCOL ERRORS
# ============================================================

class ProtocolError(Exception):
    pass


class InvalidMagicError(ProtocolError):
    pass


class UnsupportedVersionError(ProtocolError):
    pass


class UnknownMessageTypeError(ProtocolError):
    pass


class PayloadTooLargeError(ProtocolError):
    pass


class InvalidPayloadError(ProtocolError):
    pass


class InvalidRequestIdError(ProtocolError):
    pass


class IncompleteFrameError(ProtocolError):
    pass


class ExtraDataError(ProtocolError):
    pass


# ============================================================
# FRAME OBJECT
# ============================================================

@dataclass(frozen=True)
class KstpFrame:

    message_type: MessageType
    request_id: int
    payload: Dict[str, Any]
    version: int = VERSION


# ============================================================
# VALIDATION
# ============================================================

def _validate_request_id(
    request_id: int
) -> int:

    if (
        not isinstance(request_id, int)
        or isinstance(request_id, bool)
    ):
        raise InvalidRequestIdError(
            "request_id must be an integer."
        )

    if (
        request_id < 0
        or request_id > MAX_REQUEST_ID
    ):
        raise InvalidRequestIdError(
            "request_id must be between "
            "0 and 4294967295."
        )

    return request_id


def _validate_message_type(
    message_type
) -> MessageType:

    try:
        return MessageType(
            int(message_type)
        )

    except (
        TypeError,
        ValueError
    ) as exc:

        raise UnknownMessageTypeError(
            f"Unsupported message type: "
            f"{message_type}"
        ) from exc


# ============================================================
# JSON PAYLOAD
# ============================================================

def encode_payload(
    payload: Dict[str, Any]
) -> bytes:

    if not isinstance(payload, dict):

        raise InvalidPayloadError(
            "KSTP payload must be a JSON object."
        )

    try:

        payload_bytes = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":")
        ).encode(
            "utf-8"
        )

    except (
        TypeError,
        ValueError
    ) as exc:

        raise InvalidPayloadError(
            "Payload is not JSON serializable."
        ) from exc

    if len(payload_bytes) > MAX_PAYLOAD:

        raise PayloadTooLargeError(
            f"Payload size "
            f"{len(payload_bytes)} exceeds "
            f"maximum {MAX_PAYLOAD} bytes."
        )

    return payload_bytes


def decode_payload(
    payload_bytes: bytes
) -> Dict[str, Any]:

    if len(payload_bytes) > MAX_PAYLOAD:

        raise PayloadTooLargeError(
            "Payload exceeds maximum size."
        )

    try:

        payload = json.loads(
            payload_bytes.decode(
                "utf-8"
            )
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError
    ) as exc:

        raise InvalidPayloadError(
            "Payload is not valid UTF-8 JSON."
        ) from exc

    if not isinstance(payload, dict):

        raise InvalidPayloadError(
            "KSTP payload must decode "
            "to a JSON object."
        )

    return payload


# ============================================================
# FRAME ENCODER
# ============================================================

def encode_frame(
    message_type,
    request_id: int,
    payload: Dict[str, Any]
) -> bytes:

    message_type = (
        _validate_message_type(
            message_type
        )
    )

    request_id = (
        _validate_request_id(
            request_id
        )
    )

    payload_bytes = (
        encode_payload(
            payload
        )
    )

    header = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        int(message_type),
        len(payload_bytes),
        request_id
    )

    return (
        header
        + payload_bytes
    )


# ============================================================
# EXACT FRAME DECODER
# ============================================================

def decode_frame(
    frame_bytes: bytes
) -> KstpFrame:

    if len(frame_bytes) < HEADER_SIZE:

        raise IncompleteFrameError(
            "Frame does not contain "
            "a complete KSTP header."
        )

    (
        magic,
        version,
        raw_message_type,
        payload_length,
        request_id
    ) = HEADER_STRUCT.unpack(
        frame_bytes[
            :HEADER_SIZE
        ]
    )

    if magic != MAGIC:

        raise InvalidMagicError(
            "Invalid KSTP magic."
        )

    if version != VERSION:

        raise UnsupportedVersionError(
            f"Unsupported KSTP version: "
            f"{version}"
        )

    message_type = (
        _validate_message_type(
            raw_message_type
        )
    )

    _validate_request_id(
        request_id
    )

    if payload_length > MAX_PAYLOAD:

        raise PayloadTooLargeError(
            f"Declared payload size "
            f"{payload_length} exceeds "
            f"maximum {MAX_PAYLOAD}."
        )

    expected_size = (
        HEADER_SIZE
        + payload_length
    )

    if len(frame_bytes) < expected_size:

        raise IncompleteFrameError(
            "Incomplete KSTP payload."
        )

    if len(frame_bytes) > expected_size:

        raise ExtraDataError(
            "Extra bytes found after "
            "the KSTP frame."
        )

    payload_bytes = frame_bytes[
        HEADER_SIZE:
        expected_size
    ]

    payload = decode_payload(
        payload_bytes
    )

    return KstpFrame(
        message_type=message_type,
        request_id=request_id,
        payload=payload,
        version=version
    )


# ============================================================
# TCP STREAM PARSER
# ============================================================

class KstpStreamParser:
    """
    Incremental KSTP parser for a TCP byte stream.

    Handles:
        - partial headers
        - partial payloads
        - multiple frames in one recv()
    """

    def __init__(self):

        self._buffer = bytearray()

    @property
    def buffered_bytes(self) -> int:

        return len(
            self._buffer
        )

    def reset(self):

        self._buffer.clear()

    def feed(
        self,
        data: bytes
    ) -> List[KstpFrame]:

        if not isinstance(
            data,
            (
                bytes,
                bytearray,
                memoryview
            )
        ):

            raise TypeError(
                "data must be bytes-like."
            )

        self._buffer.extend(
            data
        )

        frames = []

        while True:

            # -----------------------------------------------
            # Need a complete header first.
            # -----------------------------------------------

            if len(self._buffer) < HEADER_SIZE:
                break

            (
                magic,
                version,
                raw_message_type,
                payload_length,
                request_id
            ) = HEADER_STRUCT.unpack(
                self._buffer[
                    :HEADER_SIZE
                ]
            )

            if magic != MAGIC:

                raise InvalidMagicError(
                    "Invalid KSTP magic."
                )

            if version != VERSION:

                raise UnsupportedVersionError(
                    f"Unsupported KSTP version: "
                    f"{version}"
                )

            message_type = (
                _validate_message_type(
                    raw_message_type
                )
            )

            _validate_request_id(
                request_id
            )

            if payload_length > MAX_PAYLOAD:

                raise PayloadTooLargeError(
                    f"Declared payload size "
                    f"{payload_length} exceeds "
                    f"maximum {MAX_PAYLOAD}."
                )

            frame_size = (
                HEADER_SIZE
                + payload_length
            )

            # -----------------------------------------------
            # Wait for the rest of the TCP frame.
            # -----------------------------------------------

            if len(self._buffer) < frame_size:
                break

            payload_bytes = bytes(
                self._buffer[
                    HEADER_SIZE:
                    frame_size
                ]
            )

            payload = decode_payload(
                payload_bytes
            )

            frames.append(
                KstpFrame(
                    message_type=message_type,
                    request_id=request_id,
                    payload=payload,
                    version=version
                )
            )

            del self._buffer[
                :frame_size
            ]

        return frames
