import socket
import threading

import pytest

from network.protocol import (
    HEADER_SIZE,
    HEADER_STRUCT,
    MessageType,
    decode_frame,
    encode_frame,
)

from network.tcp_server import (
    KstpTcpServer,
    NoClientConnectedError,
)


def receive_exact(
    sock,
    size
):

    data = bytearray()

    while len(data) < size:

        chunk = sock.recv(
            size - len(data)
        )

        if not chunk:

            raise RuntimeError(
                "Connection closed "
                "before enough data arrived."
            )

        data.extend(
            chunk
        )

    return bytes(
        data
    )


def receive_frame(
    sock
):

    header = receive_exact(
        sock,
        HEADER_SIZE
    )

    (
        _magic,
        _version,
        _message_type,
        payload_length,
        _request_id
    ) = HEADER_STRUCT.unpack(
        header
    )

    payload = receive_exact(
        sock,
        payload_length
    )

    return decode_frame(
        header
        + payload
    )


def test_server_receives_kstp_frame():

    received = []
    frame_event = threading.Event()

    def on_frame(frame):

        received.append(
            frame
        )

        frame_event.set()

    server = KstpTcpServer(
        host="127.0.0.1",
        port=0,
        on_frame=on_frame
    )

    server.start()

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        client.settimeout(
            2.0
        )

        client.connect(
            (
                "127.0.0.1",
                server.bound_port
            )
        )

        client.sendall(
            encode_frame(
                MessageType.ALLOCATE_LOCKER,
                1001,
                {
                    "locker_id": 17,
                    "person_id": "P10025",
                }
            )
        )

        assert frame_event.wait(
            2.0
        )

        assert len(received) == 1

        frame = received[0]

        assert (
            frame.message_type
            == MessageType.ALLOCATE_LOCKER
        )

        assert frame.request_id == 1001

        assert frame.payload == {
            "locker_id": 17,
            "person_id": "P10025",
        }

    finally:

        client.close()
        server.stop()


def test_server_handles_fragmented_tcp_data():

    received = []
    frame_event = threading.Event()

    def on_frame(frame):

        received.append(
            frame
        )

        frame_event.set()

    # recv_size=4 guarantees the server cannot consume
    # the complete frame in one recv().
    server = KstpTcpServer(
        host="127.0.0.1",
        port=0,
        recv_size=4,
        on_frame=on_frame
    )

    server.start()

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        client.settimeout(
            2.0
        )

        client.connect(
            (
                "127.0.0.1",
                server.bound_port
            )
        )

        raw = encode_frame(
            MessageType.RELEASE_LOCKER,
            2001,
            {
                "locker_id": 3,
                "person_id": "P77",
            }
        )

        client.sendall(
            raw
        )

        assert frame_event.wait(
            2.0
        )

        assert len(received) == 1

        assert (
            received[0].request_id
            == 2001
        )

        assert (
            received[0].payload[
                "person_id"
            ]
            == "P77"
        )

    finally:

        client.close()
        server.stop()


def test_server_can_send_response():

    connected_event = (
        threading.Event()
    )

    server = KstpTcpServer(
        host="127.0.0.1",
        port=0,
        on_client_connected=(
            lambda address:
            connected_event.set()
        )
    )

    server.start()

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        client.settimeout(
            2.0
        )

        client.connect(
            (
                "127.0.0.1",
                server.bound_port
            )
        )

        assert connected_event.wait(
            2.0
        )

        server.send_frame(
            MessageType.RESPONSE_OK,
            3001,
            {
                "result": "allocated"
            }
        )

        frame = receive_frame(
            client
        )

        assert (
            frame.message_type
            == MessageType.RESPONSE_OK
        )

        assert (
            frame.request_id
            == 3001
        )

        assert frame.payload == {
            "result": "allocated"
        }

    finally:

        client.close()
        server.stop()


def test_send_without_client_is_rejected():

    server = KstpTcpServer(
        host="127.0.0.1",
        port=0
    )

    server.start()

    try:

        with pytest.raises(
            NoClientConnectedError
        ):

            server.send_frame(
                MessageType.RESPONSE_OK,
                1,
                {
                    "result": "ok"
                }
            )

    finally:

        server.stop()
