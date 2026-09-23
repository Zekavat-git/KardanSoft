import hashlib
import hmac
import math
import os
import time
from enum import Enum

from PyQt5.QtCore import (
    QObject,
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
)


class UserRole(Enum):
    OPERATOR = "operator"
    ADMIN = "admin"


class AuthManager(QObject):

    accessGranted = pyqtSignal(str)

    accessDenied = pyqtSignal(
        str,
        int
    )

    authLocked = pyqtSignal(int)

    sessionChanged = pyqtSignal()

    patternChanged = pyqtSignal(str)


    PBKDF2_ITERATIONS = 200_000

    MAX_FAILED_ATTEMPTS = 5

    LOCKOUT_SECONDS = 60


    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self._operator_authenticated = False
        self._admin_authenticated = False

        self._failed_attempts = 0
        self._lockout_until = 0.0

        self._credentials = {}

        # Development defaults.
        self._set_pattern_internal(
            UserRole.OPERATOR.value,
            "1-2-5-8"
        )

        self._set_pattern_internal(
            UserRole.ADMIN.value,
            "3-2-1-4-7"
        )


    # =========================================================
    # PROPERTIES
    # =========================================================

    @pyqtProperty(
        bool,
        notify=sessionChanged
    )
    def operatorAuthenticated(
        self
    ):

        return (
            self._operator_authenticated
        )


    @pyqtProperty(
        bool,
        notify=sessionChanged
    )
    def adminAuthenticated(
        self
    ):

        return (
            self._admin_authenticated
        )


    @pyqtProperty(bool)
    def locked(
        self
    ):

        return (
            self._is_locked()
        )


    # =========================================================
    # PATTERN HELPERS
    # =========================================================

    @staticmethod
    def _normalize_pattern(
        pattern
    ):

        if pattern is None:
            return None

        text = str(
            pattern
        ).strip()

        if not text:
            return None

        parts = [
            part.strip()
            for part
            in text.split("-")
            if part.strip()
        ]

        if len(parts) < 4:
            return None

        normalized = []
        seen = set()

        for part in parts:

            if not part.isdigit():
                return None

            node = int(
                part
            )

            if (
                node < 1
                or node > 9
                or node in seen
            ):

                return None

            seen.add(
                node
            )

            normalized.append(
                str(node)
            )

        return "-".join(
            normalized
        )


    def _hash_pattern(
        self,
        pattern,
        salt
    ):

        return hashlib.pbkdf2_hmac(
            "sha256",
            pattern.encode(
                "utf-8"
            ),
            salt,
            self.PBKDF2_ITERATIONS
        )


    def _set_pattern_internal(
        self,
        role_name,
        pattern
    ):

        normalized = (
            self._normalize_pattern(
                pattern
            )
        )

        if normalized is None:
            return False

        salt = os.urandom(
            16
        )

        pattern_hash = (
            self._hash_pattern(
                normalized,
                salt
            )
        )

        self._credentials[
            role_name
        ] = {
            "salt": salt,
            "hash": pattern_hash,
        }

        return True


    def _verify_role_pattern(
        self,
        role_name,
        pattern
    ):

        normalized = (
            self._normalize_pattern(
                pattern
            )
        )

        if normalized is None:
            return False

        credential = (
            self._credentials.get(
                role_name
            )
        )

        if credential is None:
            return False

        candidate_hash = (
            self._hash_pattern(
                normalized,
                credential[
                    "salt"
                ]
            )
        )

        return hmac.compare_digest(
            candidate_hash,
            credential[
                "hash"
            ]
        )


    # =========================================================
    # LOCKOUT
    # =========================================================

    def _is_locked(
        self
    ):

        now = time.monotonic()

        if (
            self._lockout_until
            <= 0
        ):
            return False

        if (
            now
            >= self._lockout_until
        ):

            self._lockout_until = 0.0
            self._failed_attempts = 0

            return False

        return True


    def _register_failed_attempt(
        self,
        event_target
    ):

        self._failed_attempts += 1

        remaining_attempts = max(
            0,
            self.MAX_FAILED_ATTEMPTS
            - self._failed_attempts
        )

        self.accessDenied.emit(
            event_target,
            remaining_attempts
        )

        if (
            self._failed_attempts
            >= self.MAX_FAILED_ATTEMPTS
        ):

            self._lockout_until = (
                time.monotonic()
                + self.LOCKOUT_SECONDS
            )

            self._failed_attempts = 0

            self.authLocked.emit(
                self.LOCKOUT_SECONDS
            )


    def _register_success(
        self
    ):

        self._failed_attempts = 0
        self._lockout_until = 0.0


    @pyqtSlot(
        result=int
    )
    def remainingLockSeconds(
        self
    ):

        if not self._is_locked():
            return 0

        return max(
            0,
            int(
                math.ceil(
                    self._lockout_until
                    - time.monotonic()
                )
            )
        )


    # =========================================================
    # AUTHORIZATION
    # =========================================================

    @pyqtSlot(
        str,
        result=bool
    )
    def isAuthorized(
        self,
        target
    ):

        if target == "open_locker":

            return (
                self._operator_authenticated
                or self._admin_authenticated
            )

        if target == "settings":

            return (
                self._admin_authenticated
            )

        return False


    @pyqtSlot(
        str,
        str,
        result=bool
    )
    def verifyPattern(
        self,
        target,
        pattern
    ):

        if self._is_locked():

            self.authLocked.emit(
                self.remainingLockSeconds()
            )

            return False

        granted = False

        if target == "open_locker":

            if self._verify_role_pattern(
                UserRole.OPERATOR.value,
                pattern
            ):

                self._operator_authenticated = True
                granted = True

            elif self._verify_role_pattern(
                UserRole.ADMIN.value,
                pattern
            ):

                self._admin_authenticated = True
                granted = True

        elif target == "settings":

            if self._verify_role_pattern(
                UserRole.ADMIN.value,
                pattern
            ):

                self._admin_authenticated = True
                granted = True

        if granted:

            self._register_success()

            self.sessionChanged.emit()

            self.accessGranted.emit(
                target
            )

            return True

        self._register_failed_attempt(
            target
        )

        return False


    # =========================================================
    # ROLE-SPECIFIC RE-AUTHENTICATION
    # =========================================================

    @pyqtSlot(
        str,
        str,
        result=bool
    )
    def verifyRolePattern(
        self,
        role_name,
        pattern
    ):
        """
        Verify the CURRENT pattern for exactly one role.

        Unlike verifyPattern("open_locker", ...), this method does
        NOT allow the admin pattern to substitute for the operator
        pattern. It is used before changing a role's credential.
        """

        if self._is_locked():

            self.authLocked.emit(
                self.remainingLockSeconds()
            )

            return False

        if role_name not in (
            UserRole.OPERATOR.value,
            UserRole.ADMIN.value
        ):

            return False

        if self._verify_role_pattern(
            role_name,
            pattern
        ):

            self._register_success()

            return True

        self._register_failed_attempt(
            "change_pattern_"
            + role_name
        )

        return False


    # =========================================================
    # SESSION
    # =========================================================

    @pyqtSlot()
    def logoutAll(
        self
    ):

        changed = (
            self._operator_authenticated
            or self._admin_authenticated
        )

        self._operator_authenticated = False
        self._admin_authenticated = False

        if changed:
            self.sessionChanged.emit()


    # =========================================================
    # CHANGE PATTERN
    # =========================================================

    @pyqtSlot(
        str,
        str,
        result=bool
    )
    def changePattern(
        self,
        role_name,
        new_pattern
    ):

        # Settings itself requires an authenticated admin session.
        if not self._admin_authenticated:
            return False

        if role_name not in (
            UserRole.OPERATOR.value,
            UserRole.ADMIN.value
        ):

            return False

        if not self._set_pattern_internal(
            role_name,
            new_pattern
        ):

            return False

        self.patternChanged.emit(
            role_name
        )

        return True
