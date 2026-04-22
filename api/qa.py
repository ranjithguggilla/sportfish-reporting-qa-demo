from __future__ import annotations

from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import List, Tuple
from uuid import uuid4

from .db import get_conn


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))


def run_qa() -> Tuple[int, List[str]]:
    conn = get_conn()
    conn.execute("DELETE FROM qa_flags")

    issues: List[str] = []
    flag_count = 0

    catches = conn.execute("SELECT * FROM catches").fetchall()
    for c in catches:
        if not (-90 <= c["catch_lat"] <= 90 and -180 <= c["catch_lon"] <= 180):
            conn.execute(
                """
                INSERT INTO qa_flags(flag_id, record_type, record_id, flag_type, severity, score, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"flag-{uuid4().hex[:10]}",
                    "catch",
                    c["catch_id"],
                    "COORDINATE_RANGE",
                    "HIGH",
                    0.95,
                    "OPEN",
                    "Coordinate outside valid range",
                    datetime.utcnow().isoformat(),
                ),
            )
            flag_count += 1
        if c["avg_length_cm"] > 250 or c["count"] > 100:
            conn.execute(
                """
                INSERT INTO qa_flags(flag_id, record_type, record_id, flag_type, severity, score, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"flag-{uuid4().hex[:10]}",
                    "catch",
                    c["catch_id"],
                    "IMPLAUSIBLE_METRIC",
                    "MEDIUM",
                    0.7,
                    "OPEN",
                    "Length/count exceeds configured threshold",
                    datetime.utcnow().isoformat(),
                ),
            )
            flag_count += 1

    trips = conn.execute("SELECT * FROM trips").fetchall()
    for t in trips:
        st = datetime.fromisoformat(f"2000-01-01T{t['start_time']}")
        et = datetime.fromisoformat(f"2000-01-01T{t['end_time']}")
        if et <= st:
            conn.execute(
                """
                INSERT INTO qa_flags(flag_id, record_type, record_id, flag_type, severity, score, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"flag-{uuid4().hex[:10]}",
                    "trip",
                    t["trip_id"],
                    "DATETIME_ORDER",
                    "HIGH",
                    0.9,
                    "OPEN",
                    "Trip end time must be after start time",
                    datetime.utcnow().isoformat(),
                ),
            )
            flag_count += 1

    all_catches = conn.execute("SELECT * FROM catches ORDER BY trip_id, catch_time").fetchall()
    for idx, row in enumerate(all_catches):
        for other in all_catches[idx + 1 :]:
            if row["trip_id"] != other["trip_id"]:
                continue
            if row["species_code"] != other["species_code"]:
                continue
            dist = _haversine_km(row["catch_lat"], row["catch_lon"], other["catch_lat"], other["catch_lon"])
            if dist < 0.2 and abs(row["count"] - other["count"]) <= 1:
                conn.execute(
                    """
                    INSERT INTO qa_flags(flag_id, record_type, record_id, flag_type, severity, score, status, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"flag-{uuid4().hex[:10]}",
                        "catch",
                        other["catch_id"],
                        "DUPLICATE_LIKELY",
                        "MEDIUM",
                        0.65,
                        "OPEN",
                        f"Potential duplicate of {row['catch_id']}",
                        datetime.utcnow().isoformat(),
                    ),
                )
                flag_count += 1

    conn.commit()
    conn.close()
    issues.append(f"QA run complete. {flag_count} flags generated.")
    return flag_count, issues
