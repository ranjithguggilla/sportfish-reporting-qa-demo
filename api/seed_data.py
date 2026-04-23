from __future__ import annotations

import csv
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

try:
    from .db import DATA_DIR, get_conn, init_db
except ImportError:
    from db import DATA_DIR, get_conn, init_db


def _random_time() -> time:
    return time(hour=random.randint(5, 16), minute=random.choice([0, 15, 30, 45]))


def generate() -> None:
    random.seed(42)
    init_db()
    conn = get_conn()

    for table in ["anglers", "trips", "catches", "tag_reports", "qa_flags", "recapture_events"]:
        conn.execute(f"DELETE FROM {table}")

    anglers = []
    for i in range(1, 31):
        anglers.append((f"a-{i:03d}", random.choice(["PortA", "PortB", "PortC"]), random.choice(["novice", "regular", "expert"])))
    conn.executemany("INSERT INTO anglers(angler_id, home_port, experience_level) VALUES (?, ?, ?)", anglers)

    species = ["RED_SNAPPER", "COBIA", "SHARK", "TARPON", "FLOUNDER", "SNOOK"]
    trip_rows = []
    catch_rows = []
    tag_rows = []
    start_day = date(2025, 1, 1)

    for i in range(1, 241):
        trip_id = f"t-{i:04d}"
        angler_id = random.choice(anglers)[0]
        trip_date = start_day + timedelta(days=random.randint(0, 300))
        st = _random_time()
        et_hour = min(st.hour + random.randint(2, 8), 23)
        et = time(hour=et_hour, minute=st.minute)
        target_species = random.sample(species, k=random.randint(1, 3))
        trip_rows.append(
            (
                trip_id,
                angler_id,
                trip_date.isoformat(),
                random.choice(["Marker24", "BobHall", "Packery", "AransasPass"]),
                st.isoformat(),
                et.isoformat(),
                str(target_species),
                "v1",
                datetime.utcnow().isoformat(),
                "mock",
                "1.0",
            )
        )
        catches_for_trip = random.randint(2, 7)
        for c_idx in range(catches_for_trip):
            catch_id = f"c-{i:04d}-{c_idx:02d}"
            lat = round(random.uniform(26.0, 28.3), 5)
            lon = round(random.uniform(-97.8, -95.8), 5)
            count = random.randint(1, 12)
            kept = random.randint(0, count)
            released = count - kept
            catch_rows.append(
                (
                    catch_id,
                    trip_id,
                    random.choice(species),
                    count,
                    kept,
                    released,
                    round(random.uniform(20, 120), 1),
                    lat,
                    lon,
                    _random_time().isoformat(),
                    datetime.utcnow().isoformat(),
                    "mock",
                    "1.0",
                )
            )

        if i % 3 == 0:
            tag_id = f"tr-{i:04d}"
            tag_code = f"TAG{10000 + i}"
            tag_rows.append(
                (
                    tag_id,
                    trip_id,
                    tag_code,
                    "tagged",
                    random.choice(species),
                    datetime.combine(trip_date, st).isoformat(),
                    round(random.uniform(26.0, 28.3), 5),
                    round(random.uniform(-97.8, -95.8), 5),
                    random.choice(["excellent", "good", "fair"]),
                    None,
                    datetime.utcnow().isoformat(),
                    "mock",
                    "1.0",
                )
            )

            if i % 9 == 0:
                tag_rows.append(
                    (
                        f"tr-r-{i:04d}",
                        trip_id,
                        tag_code,
                        "recaptured",
                        random.choice(species),
                        datetime.combine(trip_date + timedelta(days=random.randint(5, 60)), et).isoformat(),
                        round(random.uniform(26.0, 28.3), 5),
                        round(random.uniform(-97.8, -95.8), 5),
                        random.choice(["excellent", "good", "fair", "poor"]),
                        None,
                        datetime.utcnow().isoformat(),
                        "mock",
                        "1.0",
                    )
                )

    conn.executemany(
        "INSERT INTO trips(trip_id, angler_id, trip_date, launch_site, start_time, end_time, target_species, consent_version, created_at, source_type, schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        trip_rows,
    )
    conn.executemany(
        "INSERT INTO catches(catch_id, trip_id, species_code, count, kept_count, released_count, avg_length_cm, catch_lat, catch_lon, catch_time, created_at, source_type, schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        catch_rows,
    )
    conn.executemany(
        "INSERT INTO tag_reports(tag_report_id, trip_id, tag_code, event_type, species_code, event_datetime, event_lat, event_lon, condition, photo_url, created_at, source_type, schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tag_rows,
    )
    # Deliberate edge cases for QA demonstration.
    conn.execute(
        """
        INSERT INTO catches(catch_id, trip_id, species_code, count, kept_count, released_count, avg_length_cm, catch_lat, catch_lon, catch_time, created_at, source_type, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "c-edge-invalid-coord",
            "t-0001",
            "RED_SNAPPER",
            3,
            1,
            2,
            55.0,
            95.0,
            -200.0,
            "09:00:00",
            datetime.utcnow().isoformat(),
            "mock",
            "1.0",
        ),
    )
    conn.execute(
        """
        INSERT INTO catches(catch_id, trip_id, species_code, count, kept_count, released_count, avg_length_cm, catch_lat, catch_lon, catch_time, created_at, source_type, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "c-edge-implausible",
            "t-0002",
            "COBIA",
            150,
            75,
            75,
            350.0,
            27.15,
            -96.41,
            "10:00:00",
            datetime.utcnow().isoformat(),
            "mock",
            "1.0",
        ),
    )
    conn.commit()
    conn.close()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _dump_csv()


def _dump_csv() -> None:
    conn = get_conn()
    tables = {
        "anglers.csv": "SELECT * FROM anglers",
        "trips.csv": "SELECT trip_id as tripId, angler_id as anglerId, trip_date as tripDate, launch_site as launchSite, start_time as startTime, end_time as endTime FROM trips",
        "catches.csv": "SELECT catch_id as catchId, trip_id as tripId, species_code as speciesCode, count, kept_count as keptCount, released_count as releasedCount, avg_length_cm as avgLengthCm, catch_lat as catchLat, catch_lon as catchLon, catch_time as catchTime FROM catches",
        "tag_reports.csv": "SELECT tag_report_id as tagReportId, trip_id as tripId, tag_code as tagCode, event_type as eventType, species_code as speciesCode, event_datetime as eventDateTime, event_lat as eventLat, event_lon as eventLon, condition FROM tag_reports",
    }
    for filename, query in tables.items():
        rows = conn.execute(query).fetchall()
        out = DATA_DIR / filename
        with out.open("w", newline="", encoding="utf-8") as fp:
            if not rows:
                continue
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows([dict(r) for r in rows])
    conn.close()


if __name__ == "__main__":
    generate()
    print("Seeded synthetic portal dataset.")
