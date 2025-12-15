# GymDB

GymDB is a local gym discovery and enrichment pipeline built on public OpenStreetMap (OSM) data. It performs geospatial querying, normalization, de-duplication, confidence scoring, and explainable rule-based inference to produce a clean, structured gym dataset suitable for APIs, analytics, and mobile applications.

## Overview

There is no single authoritative database of gyms.

Public datasets (including OpenStreetMap) often contain:
- Duplicate entries (nodes, ways, relations for the same location)
- Inconsistent naming and tagging
- Missing or partial business metadata

GymDB addresses these issues by implementing a deterministic data pipeline that:
1. Queries OpenStreetMap using geospatial constraints
2. Normalizes and de-duplicates gym entities
3. Scores data quality and reliability
4. Applies explainable inference rules to enrich each gym
5. Outputs a structured JSON dataset ready for downstream use

The project is intentionally designed as a backend data foundation.

## Key Features

### Geospatial Gym Discovery
- Queries OpenStreetMap via Overpass API
- Supports configurable latitude, longitude, and radius
- Collects gyms tagged as:
    - `leisure=fitness_centre`
    - `amenity=gym`
- Handles nodes, ways, and relations correctly

### Entity De-duplication
- Normalizes gym names to reduce textual variation
- Uses haversine distance calculations to detect spatial duplicates
- Merges multiple OSM references into a single canonical `Gym` entity
- Prevents over-counting the same physical location

### Confidence Scoring
Each gym receives a confidence score (0.0-1.0) based on objective-data quality signals, including:
- Presence of address information
- Website and phone metadata
- Opening hours
- Multiple independent OSM references
- Non-generic business naming

This allows downstream systems to filter or rank gyms by reliability.

## Explainable Inference Engine

GymDB separates stored facts from inferred attributes.

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
- Accompanied by explicit reasoning string explaining why each inference was made

This makes the system transparent, auditable, and easy to extend.

## Architecture

Overpass API
-> Geospatial Query 
-> Normalization & De-duplication 
-> Confidence Scoring 
-> Inference & Enrichment 
-> Structured JSON Output

Each stage is modular and independently testable.

## Output Format

The pipeline produces a structured JSON dataset where each gym includes:
- Name and location
- Aggregated OSM references
- Raw OSM tags
- Confidence score
- Inferred attributes
- Inference explanations

The format is designed for direct consumption by:
- REST APIs
- Mobile applications
- Analytics pipelines

## Usage

```bash
python main.py --lat 36.1627 --lon -86.7816 --radius-miles 30
```

### Inference Versioning

GYMDB uses a deterministic, rule-based inference engine. 
Each dataset includes inference metadata to ensure auditability and reproducibility:

- `schema_version` - JSON structure version
- `inference_meta.version` - inference ruleset version
- `inference_meta.engine` - inference engine type

This allows inference behavior to evolve without silently changing historical datasets.
