# GymDB

GymDB is a backend data platform for discovering, normalizing, and enriching gym location data using deterministic geospatial querying and explainable rule-based inference.

GymDB is intentionally designed as a **backend-first system**, not a UI-first product.

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
  All inferred attributes include readable reasoning and confidence scoring.

- **Stable, versioned APIs**
  API response shapes are treated as contracts; breaking changes require a new version.

- **Read-only public API layer**
  Public HTTP APIs never mutate database state.
  All writes occur via controlled ingestion or pipeline jobs executed through internal routes.

- **Geospatial correctness**
  All spatial queries are backed by PostGIS with proper indexing and coordinate handling.

- **Auditable job execution**
  All ingestion jobs produce immutable, deterministic receipts persisted to the database. Job outcomes can be inspected, verified, and replayed independently of runtime execution.

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
- `mypy src/gymdb api`
  Run backend type checking.
- `python scripts/profile_hotpaths.py`
  Run repeatable hot-path profiling for ingest and read-path algorithms.

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
- Changing the semantic meaning of a field or inference result.

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
  External systems and side effects: database adapters, dataset registry access, filesystem storage, and HTTP fetch clients.

- `backend/src/gymdb/infer/`
  Low-level rule engine components and inference primitives used by the domain layer.

- `backend/src/gymdb/observe/`
  Internal summaries, metrics, and audit helpers.

- `backend/api/`
  Versioned HTTP interface exposing stable, read-only views over domain outputs.

- `backend/data/`
  Published dataset artifacts, registries, and non-authoritative operational artifacts used for ingestion and offline inspection.

Each layer is independently testable and intentionally constrained.

---

## Storage Tree

GymDB keeps runtime file storage explicit and boring on purpose.

- `backend/data/registry.json`
  Region registry describing which dataset artifact belongs to which region.

- `backend/data/*.json`
  Published deterministic dataset artifacts consumed by the read-only public API.

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
2. Normalizes & Deduplicates entities
3. Scores data quality and reliability
4. Applies deterministic inference rules to enrich records
5. Publishes deterministic dataset artifacts
6. Exposes results through stable HTTP APIs

Each stage is designed to be auditable and reproducible.

---

## Example API Usage

GET /v2/gyms/geo/nearby?lat=36.1627&lon=-86.7816&radius_m=5000
