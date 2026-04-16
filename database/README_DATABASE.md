# GymDB Database Layer

> This directory documents the **physical storage contract** of GymDB.
> Anything not explicitly described here is intentionally *not* persisted.

This layer is built on **PostgreSQL + PostGIS** to support durable storage and deterministic geospatial querying.

The database is treated as a **first-class system component**, not an implementation detail. Design priorities include:
- explicit schemas and migrations
- deterministic query behavior
- safe, forward-compatible evolution
- clear separation between domain logic and persistence

The database layer enforces **physical invariants only**. It does **not** contain domain logic, inference rules, or interpretation.

---

## Goals

The database layer exists to:
- provide fast, reliable geospatial lookup (nearby queries, distance ordering)
- enforce canonical gym identity and location storage
- support forward-compatible schema evolution through migrations
- keep business logic out of SQL where possible *(SQL is used for retrieval, filtering, and spatial computation only)*

---

## Technology Stack

- **PostgreSQL**: relational storage
- **PostGIS**: spatial indexing and distance calculations
- **SQLAlchemy / query layer**: controlled, explicit query surface

---

## Current State

The database is intentionally small and explicitly defined through migrations.

At this stage:
- core tables exist to represent canonical gym records and locations
- PostGIS is enabled and spatial indexes are in place
- schema changes are applied exclusively through versioned migrations
- seed data may be used for local development and testing

The database does **not** store inferred attributes or domain interpretations.
Those remain the responsibility of the domain and inference layers.
Published dataset artifacts live on disk under `backend/data/` and are treated as a separate read-model concern.

---

## Local Development Setup

GymDB uses Docker for local database development.

### Docker Compose

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4
    container_name: gymdb-postgres
    environment:
      POSTGRES_DB: gymdb
      POSTGRES_USER: gymdb
      POSTGRES_PASSWORD: gymdb_password
    ports:
      - "5432:5432"
    volumes:
      - gymdb_pgdata:/var/lib/postgresql/data
      - ./database/schema:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gymdb -d gymdb"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  gymdb_pgdata:
```
Notes:
- PostGIS is enabled via the official postgis/postgis image
- the `schema/` directory contains migration and initialization scripts
- data is persisted across restarts using a named volume

## Data Model Overview

The database stores **physical, verifiable facts only**.

Currently represented concepts include:
- `gyms`: canonical gym records
  - stable identifier
  - name and normalized name
  - geographic location `geography(Point, 4326)`
- spatial indexes to support deterministic nearby queries
- `ops.job_receipts`: durable operational audit records

The database intentionally does **not** store:
- inference results
- confidence scores
- enriched or derived attributes
- source interpretation logic
- public dataset artifact files

These remain derived, reproducible outputs of the domain layer or filesystem-backed read models.

---

## Geospatial Querying

Nearby capabilities are exposed through the API in two forms:
- `GET /v2/gyms` with `lat`, `lon`, and `radius_m` for the canonical browser-facing contract
- `GET /v2/gyms/geo/nearby` for a narrower distance-first nearby surface

Database design requirements:
- store location as `geography(Point, 4326)` for geographic correctness
- index location using a GIST index
- add a geometry expression GIST index for KNN ordering on `location::geometry`
- use exact geography radius filtering with index-assisted nearest-neighbor ordering
- keep spatial calculations in SQL; keep inference and enrichment in Python

This gives GymDB a strong systems story:
- `ST_DWithin` enforces accurate radius membership on geography
- `ST_Distance` returns exact geographic distance
- `ORDER BY location::geometry <-> point_geometry` allows fast candidate ordering through the geometry expression index

---

## Migrations & Schema Evolution

All schema changes must be applied through migrations.

Practices:
- version migration files in the repository
- apply migrations consistently in local, CI, and deployment environments
- document breaking schema changes in the main backend README
- avoid implicit or manual schema drift

Schema stability is treated as part of the system's long-term contract.

### Running migrations

The repo includes `scripts/migrate.sh`, an ordered migration runner with applied-state tracking.
It creates a `_migrations` table on first run and skips files already recorded there, so re-running is safe.

```bash
# Apply all pending migrations (local dev defaults)
./scripts/migrate.sh

# Apply to an explicit database
./scripts/migrate.sh "postgresql://gymdb_app:gymdb_app_password@localhost:5432/gymdb"

# Include seed data (local only)
./scripts/migrate.sh --seed
```

Note: Docker Compose auto-applies schema files from `docker-entrypoint-initdb.d` only on the **first** container start (when the volume is empty). For an existing volume, use `migrate.sh` to apply new migrations.

## Design Principles
- deterministic query results
- explicit, auditable data transformations
- clear boundaries between:
  - API layer
  - query/storage layer
  - domain and inference logic
  - filesystem-backed published datasets
- safe, intentional schema evolution
