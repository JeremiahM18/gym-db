# GymDB Database Layer

This directory documents the physical storage layer for GymDB.

The database is responsible for durable facts, schema evolution, and geospatial query performance. It is not responsible for inference rules, provenance interpretation, or frontend-facing product behavior.

## Scope

The database stores:

- canonical gym records and locations
- spatial indexes for nearby querying
- operational job receipts
- schema migration history

The database does not store:

- inference outputs
- confidence scores
- derived provenance judgments
- published JSON datasets
- local runtime cache or session artifacts

Those concerns live in the domain layer or under `backend/data/`.

## Technology

- PostgreSQL 16
- PostGIS
- SQLAlchemy query layer in the backend

## Current Model

Current schema coverage includes:

- `gyms`
  - canonical identity
  - normalized name
  - `geography(Point, 4326)` location
- spatial indexes for exact radius filtering and KNN-assisted ordering
- `ops.job_receipts` for durable ingest audit records

## Query Design

Published nearby behavior is exposed through:

- `GET /v2/gyms` with `lat`, `lon`, and `radius_m`
- `GET /v2/gyms/geo/nearby` for a slimmer distance-first surface

Design requirements:

- use `geography(Point, 4326)` for geographic correctness
- keep a GIST index on location
- keep a geometry expression GIST index for KNN ordering on `location::geometry`
- use SQL for spatial filtering and distance calculations
- keep inference and enrichment logic out of SQL

This allows:

- exact radius membership with `ST_DWithin`
- exact distance with `ST_Distance`
- fast candidate ordering with `ORDER BY location::geometry <-> point_geometry`

## Migrations

Schema changes are applied through checked-in SQL files in `database/schema/`.

Local behavior:

- a fresh Docker volume auto-applies the schema files on first startup
- an existing volume requires the migration runner

Run pending migrations:

```bash
./scripts/migrate.sh
```

Apply to an explicit database:

```bash
./scripts/migrate.sh "postgresql://gymdb:gymdb_password@localhost:5432/gymdb"
```

Include seed data for local development:

```bash
./scripts/migrate.sh --seed
```

The script defaults to the local bootstrap database user so it can apply DDL and maintain `_migrations`. The backend runtime role remains `gymdb_app`.

## Local Development Notes

- Docker Compose uses `postgis/postgis:16-3.4`
- the dev seed mirrors the shipped Nashville default slice
- you can resync that dataset into a running local Postgres instance with `backend/scripts/sync_dataset_to_postgres.py`

## Documentation Ownership

Breaking schema changes should be reflected in the repo-root `README.md` when they affect local setup, migrations, or public expectations.
