# GymDB

GymDB is a local gym discovery and enrichment pipeline built on public OpenStreetMap (OSM) data. 
It provides a deterministic pipeline for geospatial querying, normalization, de-duplication, confidence scoring, and explainable rule-based inference, producing a clean and structured dataset for APIs, analytics, and mobile applications.

## Overview

There is no single authoritative database of gyms.

Public datasets (including OpenStreetMap) often suffer from:
- Duplicate entries (nodes, ways, relations representing the same location)
- Inconsistent naming and tagging conventions
- Missing or incomplete business metadata

GymDB addresses these issues by implementing a deterministic auditable data pipeline that:
1. Queries OpenStreetMap using geospatial constraints
2. Normalizes and de-duplicates gym entities
3. Scores data quality and reliability
4. Applies explainable inference rules to enrich each gym
5. Outputs a structured JSON dataset ready for downstream consumption

The project is intentionally designed as a backend data foundation, not a UI-focused application.

## Project Intent

GymDB is a deliberately engineered, end-to-end learning system.

The goal of this project is to design and build a **production-grade backend foundation** first-focusing on data quality, determinism, inference, and safe evolution-before layering on a frontend application with the same level of rigor.

This approach mirrors how real-world platforms are developed:
- Backend systems are designed for correctness, auditability, and long-term stability
- Frontend applications are built on top of reliable, well-defined data contracts

A central focus of GymDB is **rule-based inference**:
- Translating noisy real-world data into structured, explainable attributes
- Making inference decisions deterministic and auditable
- Versioning inference logic independently from schemas and APIs

By building each layer intentionally and in sequence, this project is used to gain hands-on experience with:
- Data engineering pipelines
- Inference system design
- Backend API contracts
- Versioning and backward compatibility
- Frontend integration on top of evolving data systems

## Key Features

### Geospatial Gym Discovery
- Queries OpenStreetMap via Overpass API
- Supports configurable latitude, longitude, and radius
- Collects gyms tagged as:
    - `leisure=fitness_centre`
    - `amenity=gym`
- Correctly handles nodes, ways, and relations

### Entity De-duplication
- Normalizes gym names to reduce textual variation
- Uses haversine distance calculations to detect spatial duplicates
- Merges multiple OSM references into a single canonical `Gym` entity
- Prevents over-counting the same physical location

### Confidence Scoring
Each gym receives a confidence score in the range 0.0-1.0, derived from objective-data quality signals such as:
- Presence of address information
- Website and phone metadata
- Opening hours
- Multiple independent OSM references
- Non-generic business naming

This allows downstream systems to **filter, rank, or threshold gyms by reliability**.

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
- `tier` (basic/mid/premium)

Inference is:
- Rule-based
- Deterministic
- Accompanied by explicit reasoning string explaining why each value was inferred

This design makes the system **transparent, auditable, and easy to evolve** without introducing silent behavioral changes.

## Architecture

Overpass API
 -> Geospatial Query 
 -> Normalization & De-duplication 
 -> Confidence Scoring 
 -> Inference & Enrichment 
 -> Structured JSON Output

Each stage is modular and independently testable.

## Output Format

The pipeline produces a structured JSON dataset in which each gym includes:
- Name and location
- Aggregated OSM references
- Raw OSM tags
- Confidence score
- Structured inferred attributes
- Inference explanations and metadata

The format is designed for direct consumption by:
- REST APIs
- Mobile applications
- Analytics pipelines

## Usage

```bash
python main.py --lat 36.1627 --lon -86.7816 --radius-miles 30
```

### Inference Versioning & Auditability

GYMDB uses a deterministic, rule-based inference engine with explicit versioning.

Each dataset includes inference metadata to ensure auditability and reproducibility:

- `schema_version` - JSON structure version
- `inference_meta.version` - inference ruleset version
- `inference_meta.engine` - inference engine type

This allows inference behavior to evolve over time without silently changing historical datasets.

### API Compatibility Rules

Non-breaking changes (allowed in v1):
- Adding new fields
- Adding new inference attributes
- Adding optional query parameters
- Improving inference logic without changing field meaning

Breaking changes (require v2):
- Removing fields
- Renaming fields
- Changing field types
- Changing semantic meaning of inference values

This forces long-term API discipline.

## API Versioning

GymDB uses explicit URL-based API versioning.

- `/v1` is stable and backward compatible
- Breaking changes require a new major version (`/v2`)
- Non-breaking changes may be added to `/v1`

Dataset schema versions, inference rule versions, and API versions evolve independently.

Clients should rely on:
- `api_version` for response contracts
- `schema_version` for dataset structure
- `inference_meta.version` for inference behavior

### Design Goals
- Deterministic behavior
- Explainable inference
- Clean separation of concerns
- Safe evolution over time
- Backend-first architecture

