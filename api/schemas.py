from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SpeciesCode(str, Enum):
    RED_SNAPPER = "RED_SNAPPER"
    COBIA = "COBIA"
    SHARK = "SHARK"
    TARPON = "TARPON"
    FLOUNDER = "FLOUNDER"
    SNOOK = "SNOOK"


class EventType(str, Enum):
    TAGGED = "tagged"
    RECAPTURED = "recaptured"


class FlagType(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    COORDINATE_RANGE = "COORDINATE_RANGE"
    DATETIME_ORDER = "DATETIME_ORDER"
    DUPLICATE_LIKELY = "DUPLICATE_LIKELY"
    IMPLAUSIBLE_METRIC = "IMPLAUSIBLE_METRIC"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FlagStatus(str, Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    ESCALATED = "ESCALATED"
    DISMISSED = "DISMISSED"


class TripIn(BaseModel):
    tripId: str
    anglerId: str
    tripDate: date
    launchSite: str
    startTime: time
    endTime: time
    targetSpecies: List[SpeciesCode]
    consentVersion: str


class CatchIn(BaseModel):
    catchId: str
    tripId: str
    speciesCode: SpeciesCode
    count: int = Field(ge=0)
    keptCount: int = Field(ge=0)
    releasedCount: int = Field(ge=0)
    avgLengthCm: float = Field(ge=0)
    catchLat: float
    catchLon: float
    catchTime: time


class TagReportIn(BaseModel):
    tagReportId: str
    tripId: str
    tagCode: str
    eventType: EventType
    speciesCode: SpeciesCode
    eventDateTime: datetime
    eventLat: float
    eventLon: float
    condition: str
    photoUrl: Optional[str] = None


class FlagUpdateIn(BaseModel):
    status: FlagStatus
    notes: str = ""


class ApiMessage(BaseModel):
    message: str
