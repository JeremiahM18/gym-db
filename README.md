# GymDB

GymDB is a backend data platform for discovering, normalizing, and enriching gym location data using deterministic geospatial querying, explainable rule-based inference, and coverage auditing against secondary public sources.

GymDB is intentionally designed as a **backend-first system** with a browser client that demonstrates the API and data model clearly.

The primary goal is to produce clean, auditable, and stable datasets that downstream systems can trust.

---

## Why GymDB Exists

There is no single authoritative database of gyms.

Public datasets (including OpenStreetMap) often suffer from:
- Duplicate entries (nodes, ways, relations representing the same location)
- Inconsistent naming and tagging conventions
- Missing or incomplete business metadata

GymDB exists to address these issues by building a deterministic, end-to-end pipeline that transforms noisy geospatial data into a reliable foundation for APIs, analytics, and client applications.

---

## System Guarantees

GymDB is built around explicit, enforceable guarantees:

- **Deterministic behavior**
  Identical inputs always produce identical outputs.

- **Explainable inference**
  All inferred attributes include readable reasoning, field-level confidence scoring, and contradiction diagnostics when signals disagree.

- **Stable, versioned APIs**
  API response shapes are treated as contracts; breaking changes require a new version.

- **Read-only public API layer**
  Public HTTP APIs never mutate database state.
  All writes occur via controlled ingestion or pipeline jobs executed through internal routes.

- **Geospatial correctness**
  Nearby geospatial queries use PostGIS with exact distance filtering and indexed candidate selection.
  Published dataset reads use deterministic JSON artifacts plus SQLite read-model sidecars for fast filterable API access.

- **Auditable job execution**
  All ingestion jobs produce deterministic receipts persisted to the database. Job outcomes can be inspected, verified, and replayed independently of runtime execution.

These guarantees are enforced through code structure, testing, and documented contracts.

### Contracts

- Inference contract (frozen): `docs/inference.md`
- API behavior is versioned; breaking changes require a new API version.

---

## Development Quality

GymDB treats engineering discipline as part of the product.

Backend quality workflow:
- `python -m pytest`
  Run the backend test suite.
- `ruff check .`
  Run backend linting.
- `mypy src/gymdb api scripts`
  Run backend type checking.
- `python scripts/profile_hotpaths.py`
  Run repeatable hot-path profiling for ingest and read-path algorithms.
- `python scripts/profile_service.py`
  Run concurrency and throughput profiling for dataset queries and inference.
- `python scripts/profile_postgis.py`
  Run a synthetic PostGIS query-plan profile for nearby-lookup behavior.
- `python scripts/compare_osm_tomtom.py --lat <lat> --lon <lon>`
  Run a coverage audit that compares the local OSM-derived dataset against TomTom places.

Frontend quality workflow:
- `npm run lint`
  Run frontend linting.
- `npm run build`
  Build the frontend client.

Continuous integration:
- GitHub Actions runs the same backend and frontend quality gates on pushes and pull requests.
- The backend CI job provisions PostGIS so integration tests validate against a database environment that matches production assumptions more closely.

The repo is intended to show not just working code, but deliberate architecture, test discipline, and maintainable tooling.

---

## Running The App

Backend:
- From `backend/`, install dependencies into your local virtual environment if needed.
- Start the API with:
  `.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload`
- For local frontend work without Cognito, set `ENABLE_DEV_AUTH_BYPASS=true` in `backend/.env`.
- The backend now includes CORS for the local Vite frontend origins.

Frontend:
- From `frontend/`, install dependencies with:
  `npm install`
- Start the Vite app with:
  `npm run dev`
- Open the local URL shown by Vite, typically `http://localhost:5173`

The frontend reads `VITE_API_BASE_URL` from `frontend/src/.env.local` and defaults to `http://localhost:8000`.

---

## Browser Client

The current frontend is a real demo surface, not a placeholder shell.

It supports:
- catalog browsing over `/v2/gyms`
- dataset-backed nearby search using `/v2/gyms` with `lat`, `lon`, and `radius_m`
- city/state and miles-first result cards
- website, phone, email, Google Maps, and OpenStreetMap actions when source tags exist
- a live geo canvas that projects result coordinates into an interactive map-like panel
- detailed inference inspection for a selected gym, including field-level confidence and contradiction signals
- stronger confidence scoring for richer real-world gym records like YMCA and Life Time

---

## API Stability Rules (v2)

GymDB treats its public APIs as **versioned contracts**.
Once an API version is published, its response shape and semantics are considered stable.

### Allowed Without Version Bump
The following changes are backward-compatible and may be introduced within the same API version:
- Adding new optional response fields
- Adding new inference attributes
- Adding new optional query parameters
- Internal performance or implementation improvements

### Requires a New API Version
The following changes are considered breaking and require a new API version:
- Removing existing fields
- Changing field types
- Changing the semantic meaning of a field or inference result

Breaking changes are never introduced silently.

---

## Repository Structure & Responsibility Boundaries

This repository is organized by system responsibility:

- `database/`
  Physical storage layer. Stores **verifiable facts only** and enforces hard invariants.
  No inference, no enrichment, no interpretation logic.

- `backend/src/gymdb/domain/`
  Deterministic business logic: canonical models, normalization, scoring, inference orchestration, and core constants.

- `backend/src/gymdb/application/`
  Orchestration and use cases, including ingestion workflows and job execution.

- `backend/src/gymdb/infrastructure/`
  External systems and side effects: database adapters, dataset registry access, filesystem storage, HTTP fetch clients, and comparison-source adapters like TomTom.

- `backend/src/gymdb/infer/`
  Low-level rule engine components and inference primitives used by the domain layer.

- `backend/src/gymdb/observe/`
  Internal summaries, metrics, and audit helpers.

- `backend/api/`
  Versioned HTTP interface exposing stable, read-only views over domain outputs.

- `backend/data/`
  Published dataset artifacts, registries, and non-authoritative operational artifacts used for ingestion and offline inspection.

- `frontend/`
  Browser client for browsing gyms, running nearby search, inspecting structured inference, and jumping to source-backed public actions like websites, maps, city/location views, and the geo canvas.

Each layer is independently testable and intentionally constrained.

---

## Storage Tree

GymDB keeps runtime file storage explicit and boring on purpose.

- `backend/data/registry.json`
  Region registry describing which dataset artifact belongs to which region.

- `backend/data/*.json`
  Published deterministic dataset artifacts consumed by the read-only public API. Local demo datasets are kept out of git.

- `backend/data/*.sqlite3`
  Generated SQLite read-model sidecars built during dataset publication for indexed public API reads.

- `backend/data/*.manifest.json`
  Publish manifests that tie each dataset artifact to its generated SQLite read model.

- `backend/data/artifacts/jobs/`
  Ephemeral job lifecycle snapshots used for local operational inspection.

- `backend/data/artifacts/receipts/`
  Optional filesystem copies of job receipts for debugging only.

The database remains authoritative for durable operational receipts.
Filesystem artifacts are intentionally secondary and replaceable.

---

## Architecture Overview

GymDB is intentionally backend-first and UI-agnostic.

At a high level, the system:
1. Queries raw gym data using geospatial constraints
2. Normalizes and deduplicates entities
3. Scores data quality and reliability using structured business-signal heuristics
4. Applies deterministic inference rules to enrich records, assign field-level confidence, and detect contradictory evidence
5. Publishes deterministic dataset artifacts, SQLite read-model sidecars, and publish manifests
6. Audits coverage against secondary public sources such as TomTom
7. Exposes results through stable HTTP APIs and a browser client

Each stage is designed to be auditable and reproducible.
