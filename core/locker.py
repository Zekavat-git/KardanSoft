from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LockerState(Enum):
    UNKNOWN = "unknown"
    CLOSED = "closed"
    OPEN = "open"


class ExpectedState(Enum):
    CLOSED = "closed"
    OPEN = "open"


class LockerFault(Enum):
    NONE = "none"
    UNEXPECTED_OPEN = "unexpected_open"
    FAILED_TO_OPEN = "failed_to_open"
    COMMUNICATION_LOST = "communication_lost"


class OccupancyState(Enum):
    FREE = "free"
    OCCUPIED = "occupied"


@dataclass
class Locker:
    locker_id: int
    slave_address: int
    channel: int

    # Physical state comes from hardware feedback.
    actual_state: LockerState = LockerState.UNKNOWN

    # Expected physical state comes from our own command flow.
    expected_state: ExpectedState = ExpectedState.CLOSED

    # Business/assignment state is independent from the door state.
    occupancy_state: OccupancyState = OccupancyState.FREE

    # Assignment metadata is persistent business state.
    assigned_to: Optional[str] = None
    assigned_at: Optional[str] = None

    fault: LockerFault = LockerFault.NONE

    last_command: Optional[str] = None
    last_command_time: Optional[float] = None
    last_feedback_time: Optional[float] = None
