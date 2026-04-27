# Where the Data Comes From

## Fake (generated) files

Created by `api/seed_data.py` and saved under `data/mock/`:

- `anglers.csv`
- `trips.csv`
- `catches.csv`
- `tag_reports.csv`
- `portal.db` (SQLite database)

The seed script uses a fixed random seed so repeats look the same when you reinstall.

## What is **not** included

There is **no private lab data**, **no institute data**, and **no confidential records** in this repo.

Field names match common fishing-report ideas (trip, species, GPS, counts) because that makes the demo easy to understand.

## What this demo should not be used for

This app is only for showing **software workflow**. It should not be used to claim real-world fish numbers, habitat results, or policy outcomes.
