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
- the schema/ directory contains migration and initialization scripts
- data is persisted across restarts using a named volume

## Data Model Overview

The database stores **physical, verifiable facts only**.

Currently represented concepts include:
- `gyms`: canonical gym records
    - stable identifier
    - name and normalized name
    - geographic location `geography(Point, 4326)`
- spatial indexes to support deterministic nearby queries

The database intentionally does **not** store:
- inference results
- confidence scores
- enriched or derived attributes
- source interpretation logic

These remain derived, reproducible outputs of the domain layer.

---

## Geospatial Querying

Nearby queries are exposed through API (e.g. `GET /v2/gyms/geo/nearby`).

Database design requirements:
- store location as `geography(Point, 4326)` for geographic correctness
- index location using a GIST index
- always apply explicit `ORDER BY distance` for deterministic results
- keep spatial calculations in SQL; keep inference and enrichment in Python

---

## Migrations & Schema Evolution

All schema changes must be applied through migrations.

Practices:
- version migration files in the repository
- apply migrations consistently in local, CI, and deployment environments
- document breaking schema changes in the main backend README
- avoid implicit or manual schema drift

Schema stability is treated as part of the system's long-term contract.

## Design Principles
- deterministic query results
- explicit, auditable data transformations
- clear boundaries between:
    - API layer
    - query/storage layer
    - domain and inference logic
- safe, intentional schema evolution