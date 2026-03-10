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

- `src/gymdb/`
  Domain, inference, and deterministic processing logic.

- `api/`
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

## Operational Jobs & Audit Receipts

GymDB treats ingestion and pipeline execution as first-class operational events.

Every ingestion job produces a **job receipt** - an immutable, deterministic record describing what was executed and what occurred.

### Job Receipts

A job receipt captures:
- `job_id`
- execution mode (manual, scheduled)
- target region
- start and finish timestamps
- execution status (succeeded / failed)
- structured execution statistics
- a deterministic hash derived from canonical job inputs and outputs

Receipts are:
- persisted in the database (`ops.job_receipts`)
- immutable once written
- generated for both successful and failed jobs
- suitable for replay verification and regression detection

The database is the **authoritative source of truth** for job receipts.
Optional filesystem artifacts may be written for debugging, but are never authoritative.

### Separation of Concerns

GymDB deliberately separates:
- **Job lifecycle state** (queued / running / failed)
- **Job outcome artifacts** (receipts)

Lifecycle state is ephemeral and implementation-specific.
Receipts are durable audit artifacts intended for long-term inspection and verification.

This separation ensures that operational correctness does not depend on runtime state.

---

## Core Capabilities

### Geospatial Gym Discovery
- Queries OpenStreetMap via the Overpass API
- Configurable latitude, longitude, and radius
- Collects gyms tagged as:
    - `leisure=fitness_centre`
    - `amenity=gym`
- Handles nodes, ways, and relations uniformly

### Entity Deduplication
- Normalizes gym names to reduce textual variation
- Uses haversine distance to detect spatial duplicates
- Merges multiple OSM references into a single canonical gym record
- Prevents over-counting the same physical location

### Confidence Scoring
Each gym receives a confidence score (0.0-1.0) derived from objective data-quality signals, including:
- Address presence
- Website and phone metadata
- Opening hours
- Multiple independent OSM references
- Non-generic business naming

Downstream systems can filter, rank, or threshold gyms by reliability.

---

## Explainable Inference Engine

GymDB separates **stored facts** from **inferred attributes**.

**Stored facts**
- Raw OSM tags
- Geographic coordinates
- OSM element references

**Inferred attributes**
- `is_24_7`
- `premium_score`
- `lifter_friendly`
- `tier` (basic / mid / premium)
- Additional structured signals

Inference is:
- Rule-based
- Deterministic
- Accompanied by explicit reasons for each inferred value

This design makes the inference behavior transparent, auditable, and safe to evolve over time.

The authoritative contract for inference behavior and invariants lives in `docs/inference.md`.

---

## Embedding-Ready API Views

GymDB includes an embedding-oriented API view designed for downstream semantic systems.

Embeddings are **not generated by GymDB itself**. Instead, the backend exposes:
- A deterministic, text-based representation of each gym
- Structured inference metadata alongside the embedding text

This allows external systems (search, ML models, vector databases) to:
- Generate embeddings consistently
- Reproduce embeddings deterministically
- Trace semantic representations back to explainable inference

Embedding views are treated as a **derived API representation**, not core domain data.

---

## API Design & Routing

GymDB follows strict REST and namespace discipline.
- Core entities and collections live under:
    - /v2/gyms
    - /v2/gyms/{gym_id}
- Geospatial queries are namespaced separately:
    - /v2/gyms/geo/nearby

This avoids route collisions, eliminates ambiguity, and scales cleanly as new query types are added (bounding boxes, routes, analytics).

### Internal Operational Routes

GymDB exposes a small set of **internal, gated routes** used for operational control and observability. These routes are not part of the public API contract.

Examples:
- `/internal/jobs/ingest` - trigger ingestion jobs
- `/internal/jobs/{job_id}` - inspect job receipts
- `/internal/jobs` - list recent job executions

Internal routes:
- are disabled by default
- require explicit enablement
- require administrative authorization
- are intended for operators, not clients

This separation preserves API stability while enabling operational control.

---

## Observability & Metrics

GymDB exposes lightweight internal observability endpoints to support debugging, validation, and inference monitoring.

### Health & Readiness
- `/healthz`: Liveness probe (process is running)
- `/readyz`: Readiness probe (external dependencies reachable)

### Inference Metrics
- `/metrics/inference`: Reports which inference rules have fired and how often

Metrics are intended for internal use and are not part of the public API contract. They provide visibility into inference behavior without coupling metrics to domain logic or persistence.

---

## Versioning & Compatibility

### Versioning
GymDB versions three concerns independently:
- API version (`api_version`): response contract
- Dataset schema version (`schema_version`): structure of stored/output data
- Inference version (`inference_meta.version`): behavior of inference rules

### Compatibility Rules
Non-breaking changes (allowed within a version):
- Adding new fields
- Adding new inference attributes
- Adding optional query parameters
- Improving inference logic without changing semantic meaning

Breaking changes (require a new version):
- Removing fields
- Renaming fields
- Changing field types
- Changing semantic meaning of inference values

This forces long-term API discipline and safe evolution.

---

## Running & Testing

The backend is considered valid only when all tests pass.

Tests enforce:
- Deterministic inference behavior
- Stable API response shapes
- Correct geospatial query behavior
- Dependency and boundary correctness

This ensures changes do not silently violate system guarantees.

### Database Integration Tests

GymDB includes database-backed integration tests that validate persistence, schema invariants, and deterministic behavior.

Integration tests:
- use a dedicated test database
- validate job receipt round-trip persistence
- ensure database constraints enforce system guarantees
- run independently of API-level dependency overrides

This ensures that operational audit behavior is verified against real database semantics.

---

## Database Foundations (Migration 001)

GymDB’s initial database migration is intentionally minimal.

Migration 001 establishes only the **physical invariants** required for the system:
- Canonical gym identity
- Geospatial storage and indexing
- Deterministic nearby queries

It does **not** include:
- Inference results
- Confidence scores
- Tags or enrichment data
- Source-specific metadata

This is a deliberate design choice.

Inference, enrichment, and confidence scoring are treated as **derived domain logic**, not stored facts. Encoding those concepts at the database layer too early would:
- Prematurely lock in inference semantics
- Conflate raw data with interpretation
- Increase long-term schema migration risk

Instead, GymDB follows a layered approach:

- **Database**: stores physical facts and enforces hard invariants
- **Published dataset artifacts**: store deterministic read models for the public API
- **Domain layer**: performs normalization, deduplication, and inference
- **API layer**: exposes stable, versioned representations

This allows the inference system to evolve independently of the database schema while preserving auditability and determinism.

### Operational Metadata (Migration 002)

Migration 002 introduces an `ops` schema used exclusively for operational metadata.

This schema includes:
- `job_receipts`: immutable records of ingestion job execution

Operational metadata is intentionally separated from domain data to:
- avoid polluting core schemas
- preserve clear ownership boundaries
- allow operational tooling to evolve independently

The `ops` schema is not exposed through public APIs and exist solely to support auditability, replay verification, and operational introspection.

---

## Design Philosophy

GymDB prioritizes correctness, determinism, and explainability over convenience.

The goal is a backend foundation that can be trusted, audited, and safely extended as the system grows.

GymDB is an end-to-end learning system built to mirror real platform development:
- Backend systems prioritize correctness, determinism, auditability, and long-term stability
- Frontend applications are layered on top of stable versioned data contracts
- APIs are treated as products with explicit compatibility rules

A central focus of GymDB is **rule-based inference**:
- Translating noisy real-world data into structured attributes
- Making inference decisions deterministic and explainable
- Versioning inference logic independently from API and dataset schemas

The project is built incrementally, with each layer added deliberately to gain experience with enterprise backend design, testing discipline, and API evolution.

---

## Example API Usage

GET /v2/gyms/geo/nearby?lat=36.1627&lon=-86.7816&radius_m=5000
