# Build Notes

Short notes about why the demo is shaped this way.

## What we kept in version 1

- Focus on clear forms, checks, review queue, and downloads.
- Use only fake data so anyone can run it safely.

## What we skipped on purpose

- Big science models or stock estimates.
- Heavy mapping/GIS beyond a simple preview map.

## How the pieces fit

- FastAPI + SQLite so one laptop can run everything.
- Plain HTML pages so the UI is easy to change.
- A seed script so demo numbers always look familiar.
