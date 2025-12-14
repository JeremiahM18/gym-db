# GymDB

A local gym database built from public OpenStreetMap data using geospatial querying, normalization, and de-duplication.

## Overview

GymDB is a backend data pipeline that discovers gyms within a specified geographic radius and produces a clean, structured dataset suitable for APIs and mobile applications.

There is no single authoritative database of gyms, and publicly available data often contains duplicate entries and inconsistencies. This project addresses those issues by combining geospatial querying with normalization and distance-based de-duplication.

