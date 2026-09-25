import sqlite3
from pathlib import Path
from typing import Optional


class LockerDatabase:
    """
    Small SQLite persistence layer for locker assignment state.

    assigned_to stores the person's unique ID.

    Physical door state and faults are intentionally NOT persisted.
    After a real device reboot they must come from fresh hardware feedback.
    """

    def __init__(self, database_path):

        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._connection = sqlite3.connect(
            str(self.database_path)
        )

        self._connection.row_factory = (
            sqlite3.Row
        )

        self._create_schema()

    # =========================================================
    # SCHEMA
    # =========================================================

    def _create_schema(self):

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locker_assignments (
                locker_id INTEGER PRIMARY KEY,
                assigned_to TEXT,
                assigned_at TEXT NOT NULL
            )
            """
        )

        self._connection.commit()

    # =========================================================
    # ASSIGNMENT
    # =========================================================

    def assign_locker(
        self,
        locker_id: int,
        assigned_to: Optional[str] = None
    ):

        if assigned_to is not None:

            assigned_to = str(
                assigned_to
            ).strip()

            if not assigned_to:

                raise ValueError(
                    "assigned_to must not be empty."
                )

        self._connection.execute(
            """
            INSERT INTO locker_assignments (
                locker_id,
                assigned_to,
                assigned_at
            )
            VALUES (
                ?,
                ?,
                datetime('now')
            )
            ON CONFLICT(locker_id)
            DO UPDATE SET
                assigned_to = excluded.assigned_to,
                assigned_at = excluded.assigned_at
            """,
            (
                int(locker_id),
                assigned_to,
            )
        )

        self._connection.commit()

    def release_locker(
        self,
        locker_id: int
    ):

        cursor = self._connection.execute(
            """
            DELETE FROM locker_assignments
            WHERE locker_id = ?
            """,
            (
                int(locker_id),
            )
        )

        self._connection.commit()

        return cursor.rowcount > 0

    # =========================================================
    # QUERY
    # =========================================================

    def get_assignment(
        self,
        locker_id: int
    ):

        row = self._connection.execute(
            """
            SELECT
                locker_id,
                assigned_to,
                assigned_at
            FROM locker_assignments
            WHERE locker_id = ?
            """,
            (
                int(locker_id),
            )
        ).fetchone()

        if row is None:
            return None

        return {
            "locker_id":
                int(row["locker_id"]),

            "assigned_to":
                row["assigned_to"],

            "assigned_at":
                row["assigned_at"],
        }

    def get_all_assignments(self):

        rows = self._connection.execute(
            """
            SELECT
                locker_id,
                assigned_to,
                assigned_at
            FROM locker_assignments
            ORDER BY locker_id
            """
        ).fetchall()

        return [
            {
                "locker_id":
                    int(row["locker_id"]),

                "assigned_to":
                    row["assigned_to"],

                "assigned_at":
                    row["assigned_at"],
            }
            for row in rows
        ]

    def find_by_assigned_to(
        self,
        assigned_to: str
    ):

        assigned_to = str(
            assigned_to
        ).strip()

        if not assigned_to:
            return None

        row = self._connection.execute(
            """
            SELECT
                locker_id,
                assigned_to,
                assigned_at
            FROM locker_assignments
            WHERE assigned_to = ?
            LIMIT 1
            """,
            (
                assigned_to,
            )
        ).fetchone()

        if row is None:
            return None

        return {
            "locker_id":
                int(row["locker_id"]),

            "assigned_to":
                row["assigned_to"],

            "assigned_at":
                row["assigned_at"],
        }

    def assignment_matches(
        self,
        locker_id: int,
        assigned_to: str
    ) -> bool:

        assignment = self.get_assignment(
            locker_id
        )

        if assignment is None:
            return False

        return (
            assignment["assigned_to"]
            == str(assigned_to).strip()
        )

    # =========================================================
    # LIFECYCLE
    # =========================================================

    def close(self):

        if self._connection is not None:

            self._connection.close()

            self._connection = None
