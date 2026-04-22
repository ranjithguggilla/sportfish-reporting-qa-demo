from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .db import ROOT, get_conn, init_db
from .qa import run_qa
from .schemas import CatchIn, FlagUpdateIn, TagReportIn, TripIn


app = FastAPI(title="Reporting and Tagging Intelligence Portal")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = ROOT / "frontend"
EXPORT_DIR = ROOT / "data" / "mock" / "exports"


def _role_from_request(request: Request) -> str:
    header_role = request.headers.get("x-role")
    query_role = request.query_params.get("role")
    return (header_role or query_role or "angler").lower()


def require_analyst(request: Request) -> str:
    role = _role_from_request(request)
    if role != "analyst":
        raise HTTPException(status_code=403, detail="Analyst role required")
    return role


@app.on_event("startup")
def startup() -> None:
    init_db()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/submit-trip")
def submit_trip_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "submit-trip.html")


@app.get("/my-contributions")
def contributions_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "my-contributions.html")


@app.get("/analyst/queue")
def analyst_queue_page(request: Request):
    if _role_from_request(request) != "analyst":
        return RedirectResponse(url="/?denied=analyst", status_code=303)
    return FileResponse(FRONTEND_DIR / "analyst-queue.html")


@app.get("/analyst/exports")
def analyst_exports_page(request: Request):
    if _role_from_request(request) != "analyst":
        return RedirectResponse(url="/?denied=analyst", status_code=303)
    return FileResponse(FRONTEND_DIR / "analyst-exports.html")


@app.get("/analyst/record/{record_type}/{record_id}")
def analyst_record_page(record_type: str, record_id: str, request: Request):
    if _role_from_request(request) != "analyst":
        return RedirectResponse(url="/?denied=analyst", status_code=303)
    _ = (record_type, record_id)
    return FileResponse(FRONTEND_DIR / "analyst-record.html")


@app.get("/recaptures/{tag_code}")
def recaptures_page(tag_code: str) -> FileResponse:
    _ = tag_code
    return FileResponse(FRONTEND_DIR / "recaptures.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.post("/api/v1/trips")
def create_trip(payload: TripIn) -> dict:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO trips(trip_id, angler_id, trip_date, launch_site, start_time, end_time, target_species, consent_version, created_at, source_type, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.tripId,
                payload.anglerId,
                payload.tripDate.isoformat(),
                payload.launchSite,
                payload.startTime.isoformat(),
                payload.endTime.isoformat(),
                json.dumps([s.value for s in payload.targetSpecies]),
                payload.consentVersion,
                datetime.utcnow().isoformat(),
                "manual",
                "1.0",
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        if "UNIQUE constraint failed: trips.trip_id" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Trip ID already exists. Click 'Load Demo Values' to generate a new ID, or choose a different tripId.",
            ) from exc
        raise HTTPException(status_code=400, detail=f"Unable to create trip: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to create trip: {exc}") from exc
    finally:
        conn.close()
    return {"message": "Trip created", "tripId": payload.tripId}


@app.post("/api/v1/catches")
def create_catch(payload: CatchIn) -> dict:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO catches(catch_id, trip_id, species_code, count, kept_count, released_count, avg_length_cm, catch_lat, catch_lon, catch_time, created_at, source_type, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.catchId,
                payload.tripId,
                payload.speciesCode.value,
                payload.count,
                payload.keptCount,
                payload.releasedCount,
                payload.avgLengthCm,
                payload.catchLat,
                payload.catchLon,
                payload.catchTime.isoformat(),
                datetime.utcnow().isoformat(),
                "manual",
                "1.0",
            ),
        )
        conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to create catch: {exc}") from exc
    finally:
        conn.close()
    return {"message": "Catch created", "catchId": payload.catchId}


@app.post("/api/v1/tag-reports")
def create_tag_report(payload: TagReportIn) -> dict:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO tag_reports(tag_report_id, trip_id, tag_code, event_type, species_code, event_datetime, event_lat, event_lon, condition, photo_url, created_at, source_type, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.tagReportId,
                payload.tripId,
                payload.tagCode,
                payload.eventType.value,
                payload.speciesCode.value,
                payload.eventDateTime.isoformat(),
                payload.eventLat,
                payload.eventLon,
                payload.condition,
                payload.photoUrl,
                datetime.utcnow().isoformat(),
                "manual",
                "1.0",
            ),
        )
        conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to create tag report: {exc}") from exc
    finally:
        conn.close()
    return {"message": "Tag report created", "tagReportId": payload.tagReportId}


@app.get("/api/v1/trips/{trip_id}")
def get_trip(trip_id: str) -> dict:
    conn = get_conn()
    trip = conn.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id,)).fetchone()
    catches = conn.execute("SELECT * FROM catches WHERE trip_id = ?", (trip_id,)).fetchall()
    tags = conn.execute("SELECT * FROM tag_reports WHERE trip_id = ?", (trip_id,)).fetchall()
    conn.close()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"trip": dict(trip), "catches": [dict(c) for c in catches], "tagReports": [dict(t) for t in tags]}


@app.get("/api/v1/demo/ids")
def demo_ids() -> dict:
    conn = get_conn()
    sample_trip = conn.execute("SELECT trip_id FROM trips ORDER BY trip_id LIMIT 1").fetchone()
    sample_tag = conn.execute("SELECT tag_code FROM tag_reports ORDER BY tag_code LIMIT 1").fetchone()
    sample_species = conn.execute("SELECT DISTINCT species_code FROM catches ORDER BY species_code").fetchall()
    conn.close()
    return {
        "sampleTripId": sample_trip["trip_id"] if sample_trip else None,
        "sampleTagCode": sample_tag["tag_code"] if sample_tag else None,
        "speciesCodes": [r["species_code"] for r in sample_species],
    }


@app.get("/api/v1/tag-reports/{tag_code}/history")
def get_tag_history(tag_code: str) -> dict:
    conn = get_conn()
    history = conn.execute(
        "SELECT * FROM tag_reports WHERE tag_code = ? ORDER BY event_datetime ASC", (tag_code,)
    ).fetchall()
    conn.close()
    return {"tagCode": tag_code, "history": [dict(h) for h in history]}


@app.get("/api/v1/trips/{trip_id}/layers")
def get_trip_layers(
    trip_id: str,
    species: Optional[str] = Query(default=None),
    includeFlags: bool = Query(default=True),
    includeTags: bool = Query(default=True),
) -> dict:
    conn = get_conn()
    catch_query = "SELECT * FROM catches WHERE trip_id = ?"
    params: list = [trip_id]
    if species:
        catch_query += " AND species_code = ?"
        params.append(species)
    catches = conn.execute(catch_query, tuple(params)).fetchall()
    tags = conn.execute("SELECT * FROM tag_reports WHERE trip_id = ? ORDER BY event_datetime", (trip_id,)).fetchall() if includeTags else []
    flag_rows = []
    if includeFlags:
        catch_ids = [c["catch_id"] for c in catches]
        if catch_ids:
            placeholders = ",".join(["?"] * len(catch_ids))
            flag_rows = conn.execute(
                f"SELECT * FROM qa_flags WHERE record_type='catch' AND record_id IN ({placeholders})",
                tuple(catch_ids),
            ).fetchall()
    conn.close()
    return {
        "tripId": trip_id,
        "catches": [dict(c) for c in catches],
        "tags": [dict(t) for t in tags],
        "flags": [dict(f) for f in flag_rows],
    }


@app.post("/api/v1/qa/run")
def qa_run(_: str = Depends(require_analyst)) -> dict:
    count, details = run_qa()
    return {"message": "QA run complete", "flagCount": count, "details": details}


@app.get("/api/v1/qa/flags")
def list_flags(
    status: Optional[str] = Query(default=None),
    flagType: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    fromDate: Optional[str] = Query(default=None),
    toDate: Optional[str] = Query(default=None),
    _: str = Depends(require_analyst),
) -> dict:
    conn = get_conn()
    query = "SELECT * FROM qa_flags WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if flagType:
        query += " AND flag_type = ?"
        params.append(flagType)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if fromDate:
        query += " AND date(created_at) >= date(?)"
        params.append(fromDate)
    if toDate:
        query += " AND date(created_at) <= date(?)"
        params.append(toDate)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@app.patch("/api/v1/qa/flags/{flag_id}")
def update_flag(flag_id: str, payload: FlagUpdateIn, _: str = Depends(require_analyst)) -> dict:
    conn = get_conn()
    updated = conn.execute(
        "UPDATE qa_flags SET status = ?, notes = ? WHERE flag_id = ?",
        (payload.status.value, payload.notes, flag_id),
    )
    conn.commit()
    conn.close()
    if updated.rowcount == 0:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"message": "Flag updated", "flagId": flag_id}


@app.get("/api/v1/records/{record_type}/{record_id}")
def get_record(record_type: str, record_id: str, _: str = Depends(require_analyst)) -> dict:
    table_map = {"trip": "trips", "catch": "catches", "tag": "tag_reports", "tag_report": "tag_reports"}
    id_map = {"trip": "trip_id", "catch": "catch_id", "tag": "tag_report_id", "tag_report": "tag_report_id"}
    if record_type not in table_map:
        raise HTTPException(status_code=400, detail="Unsupported record_type")

    conn = get_conn()
    row = conn.execute(
        f"SELECT * FROM {table_map[record_type]} WHERE {id_map[record_type]} = ?",
        (record_id,),
    ).fetchone()
    flags = conn.execute(
        "SELECT * FROM qa_flags WHERE record_type = ? AND record_id = ? ORDER BY created_at DESC",
        (record_type if record_type != "tag" else "tag_report", record_id),
    ).fetchall()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"recordType": record_type, "record": dict(row), "flags": [dict(f) for f in flags]}


def _export_rows() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT c.catch_id, c.trip_id, t.angler_id, t.trip_date, c.species_code, c.count, c.kept_count, c.released_count,
               c.avg_length_cm, c.catch_lat, c.catch_lon, c.catch_time
        FROM catches c JOIN trips t ON c.trip_id = t.trip_id
        """
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        row = dict(r)
        hour = int(str(row["catch_time"]).split(":")[0])
        row["weatherWindow"] = "calm" if hour < 10 else "mixed" if hour < 14 else "windy"
        out.append(row)
    return out


@app.get("/api/v1/exports/reports.csv")
def export_csv(_: str = Depends(require_analyst)) -> FileResponse:
    rows = _export_rows()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / "reports.csv"
    if rows:
        with path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        path.write_text("", encoding="utf-8")
    return FileResponse(path, filename="reports.csv")


@app.get("/api/v1/exports/reports.geojson")
def export_geojson(_: str = Depends(require_analyst)) -> JSONResponse:
    rows = _export_rows()
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["catch_lon"], r["catch_lat"]]},
            "properties": {k: v for k, v in r.items() if k not in {"catch_lat", "catch_lon"}},
        }
        for r in rows
    ]
    data = {"type": "FeatureCollection", "features": features}
    return JSONResponse(content=data)


@app.get("/api/v1/exports/qa-summary.json")
def export_qa_summary(_: str = Depends(require_analyst)) -> dict:
    conn = get_conn()
    rows = conn.execute(
        "SELECT flag_type, severity, COUNT(*) AS total FROM qa_flags GROUP BY flag_type, severity"
    ).fetchall()
    conn.close()
    return {
        "generatedAt": datetime.utcnow().isoformat(),
        "summary": [dict(r) for r in rows],
    }
