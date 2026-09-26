from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

from network.protocol import (
    KstpFrame,
    MessageType,
)


OpenHandler = Callable[
    [int],
    Tuple[bool, str]
]


@dataclass(frozen=True)
class CommandResponse:

    message_type: MessageType
    request_id: int
    payload: Dict[str, Any]


class CommandHandler:
    """
    Converts decoded KSTP request frames into application
    business operations.

    This class deliberately contains:
        - no socket code
        - no QML code
        - no hardware transport code

    OPEN commands use an injected callback so that the final
    application can route them through LockerController.
    """

    def __init__(
        self,
        locker_manager,
        open_handler: Optional[
            OpenHandler
        ] = None
    ):

        self._locker_manager = (
            locker_manager
        )

        self._open_handler = (
            open_handler
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def handle(
        self,
        frame: KstpFrame
    ) -> CommandResponse:

        if (
            frame.message_type
            == MessageType.ALLOCATE_LOCKER
        ):

            return self._handle_allocate(
                frame
            )

        if (
            frame.message_type
            == MessageType.OPEN_LOCKER
        ):

            return self._handle_open(
                frame
            )

        if (
            frame.message_type
            == MessageType.RELEASE_LOCKER
        ):

            return self._handle_release(
                frame
            )

        return self._error(
            frame.request_id,
            "unsupported_request_type"
        )

    # ========================================================
    # ALLOCATE
    # ========================================================

    def _handle_allocate(
        self,
        frame: KstpFrame
    ) -> CommandResponse:

        locker_id = self._get_locker_id(
            frame.payload
        )

        if locker_id is None:

            return self._error(
                frame.request_id,
                "invalid_locker_id"
            )

        person_id = self._get_person_id(
            frame.payload
        )

        if person_id is None:

            return self._error(
                frame.request_id,
                "invalid_person_id",
                locker_id
            )

        try:

            (
                success,
                result
            ) = (
                self._locker_manager
                .allocate_to_person(
                    locker_id,
                    person_id
                )
            )

        except Exception:

            return self._error(
                frame.request_id,
                "internal_error",
                locker_id
            )

        return self._business_result(
            frame.request_id,
            locker_id,
            success,
            result
        )

    # ========================================================
    # RELEASE
    # ========================================================

    def _handle_release(
        self,
        frame: KstpFrame
    ) -> CommandResponse:

        locker_id = self._get_locker_id(
            frame.payload
        )

        if locker_id is None:

            return self._error(
                frame.request_id,
                "invalid_locker_id"
            )

        person_id = self._get_person_id(
            frame.payload
        )

        if person_id is None:

            return self._error(
                frame.request_id,
                "invalid_person_id",
                locker_id
            )

        try:

            (
                success,
                result
            ) = (
                self._locker_manager
                .release_from_person(
                    locker_id,
                    person_id
                )
            )

        except Exception:

            return self._error(
                frame.request_id,
                "internal_error",
                locker_id
            )

        return self._business_result(
            frame.request_id,
            locker_id,
            success,
            result
        )

    # ========================================================
    # OPEN
    # ========================================================

    def _handle_open(
        self,
        frame: KstpFrame
    ) -> CommandResponse:

        locker_id = self._get_locker_id(
            frame.payload
        )

        if locker_id is None:

            return self._error(
                frame.request_id,
                "invalid_locker_id"
            )

        if self._open_handler is None:

            return self._error(
                frame.request_id,
                "open_handler_unavailable",
                locker_id
            )

        try:

            result = self._open_handler(
                locker_id
            )

        except Exception:

            return self._error(
                frame.request_id,
                "internal_error",
                locker_id
            )

        if (
            not isinstance(result, tuple)
            or len(result) != 2
        ):

            return self._error(
                frame.request_id,
                "invalid_open_handler_result",
                locker_id
            )

        (
            success,
            result_code
        ) = result

        if not isinstance(
            success,
            bool
        ):

            return self._error(
                frame.request_id,
                "invalid_open_handler_result",
                locker_id
            )

        if (
            not isinstance(
                result_code,
                str
            )
            or not result_code.strip()
        ):

            return self._error(
                frame.request_id,
                "invalid_open_handler_result",
                locker_id
            )

        return self._business_result(
            frame.request_id,
            locker_id,
            success,
            result_code.strip()
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _get_locker_id(
        payload: Dict[str, Any]
    ) -> Optional[int]:

        locker_id = payload.get(
            "locker_id"
        )

        # bool is a subclass of int in Python,
        # so reject it explicitly.
        if (
            not isinstance(
                locker_id,
                int
            )
            or isinstance(
                locker_id,
                bool
            )
        ):

            return None

        if locker_id <= 0:

            return None

        return locker_id

    @staticmethod
    def _get_person_id(
        payload: Dict[str, Any]
    ) -> Optional[str]:

        person_id = payload.get(
            "person_id"
        )

        if not isinstance(
            person_id,
            str
        ):

            return None

        person_id = (
            person_id.strip()
        )

        if not person_id:

            return None

        return person_id

    # ========================================================
    # RESPONSE BUILDERS
    # ========================================================

    @staticmethod
    def _business_result(
        request_id: int,
        locker_id: int,
        success: bool,
        result: str
    ) -> CommandResponse:

        if success:

            return CommandResponse(
                message_type=(
                    MessageType.RESPONSE_OK
                ),
                request_id=request_id,
                payload={
                    "result": result,
                    "locker_id": locker_id,
                }
            )

        return CommandResponse(
            message_type=(
                MessageType.RESPONSE_ERROR
            ),
            request_id=request_id,
            payload={
                "error": result,
                "locker_id": locker_id,
            }
        )

    @staticmethod
    def _error(
        request_id: int,
        error: str,
        locker_id: Optional[
            int
        ] = None
    ) -> CommandResponse:

        payload = {
            "error": error
        }

        if locker_id is not None:

            payload[
                "locker_id"
            ] = locker_id

        return CommandResponse(
            message_type=(
                MessageType.RESPONSE_ERROR
            ),
            request_id=request_id,
            payload=payload
        )
