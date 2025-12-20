# GymDB Database

This directory contains the **database layer** for GymDB, built on **PostgreSQL + PostGIS** to support durable storage and geospatial queries.

The database is treated as a **first-class system component**, not an implementation detail. Design priorities include:
- Explicit schemas and migrations
- Deterministic query behavior
- Safe, forward-compatible evolution
- Clear separation between domain logic and persistence

At the current stage, the database is intentionally minimal and focused on infrastructure setup rather than finalized schema design.

## Goals

- Provide fast, reliable geospatial lookup (nearby queries, distance ordering)
- Persist normalized/enriched gym records and derived attributes
- Support stable API contracts with forward-compatibe schema evolution
- Keep business logic out of SQL where possible *(SQL is used for retrieval, filtering, and spatial computation only)*

## Technology Stack

- **PostgreSQL**: relational storage
- **PostGIS**: spatial indexing and distance calculations
- **SQLAchemy / queries module**: controlled, explicit query surface

## Current State

The database is **not yet populated with application tables**.

At this stage:
- The schema directory is intentionally empty
- No production tables are defined yet
- The focus is on standing up a correct, repeatable Postgres + PostGIS environment for future development

This is a deliberate choice to avoid premature schema commitments.

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
- PostGIS is enabled via the official postgis/postgis image
- The schema/ directory is mounted for future initialization scripts
- Data is persisted across restarts using a named volume

## Planned Data Model

The following concepts are expected to be represented once schema design begins:
- `gyms`: Canonical gym records (id, name, normalized name, latitude/longitude, etc.)
- `osm_refs` (or embedded references): Source provenance for OpenStreetMap elements (node/way/relation IDs)
- `tags` (optional): Retained raw OSM tags for traceability and auditing
- `inference` (optional): Structured inferred attributes with reasons and confidence metadata
- `confidence`: Numeric reliability score(0.0-1.0)

Exact tables, columns, and relationships will be introduced via migrations and reflected in the API contract when finalized.

## Geospatial Querying

Nearby queries are exposed through API, for example:

GET /v2/gyms/geo/nearby

Implementation notes:
- Store location as a PostGIS `geography(Point, 4326)`
- Index geoetry using a GIST or SP-GIST index
- Always apply explicit `Order BY distance` for deterministic results
- Keep spatial calculations in SQL; keep inference and enrichment in Python

## Migrations & Schema Evolution

All schema changes must be applied through migrations.

Recommended practices:
- Version migration files in the repository
- Apply migrations in CI and deployment pipelines
- Document breaking schema changes in the main project README
- Avoid implicit or manual schema drift

Schema stability is treated as part of the public contract of the system.

## Design Principles
- Deterministic query results
- Explicit, auditable data transformations
- Clear boundaries between:
    - API layer
    - Query/storage layer
    - Domain and inference logic
- Safe, intentional schema evolution