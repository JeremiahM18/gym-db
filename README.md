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

### Design Goals
- Deterministic behavior
- Explainable inference
- Clean separation of concerns
- Safe evolution over time
- Backend-first architecture