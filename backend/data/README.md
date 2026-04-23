# Backend Data

This directory contains two categories of files:

- tracked dataset fixtures and shipped demo data
- ignored local runtime artifacts

## Tracked

Tracked files are small, intentional, and safe to review in git. They include:

- dataset registry files such as `registry.json`
- shipped demo datasets such as the Nashville default slice
- tiny test fixtures used by automated tests
- this README

## Ignored

Ignored files are generated locally and should not be committed. They include:

- regenerated datasets and manifests
- SQLite sidecars and lock files
- live-search cache files under `live_search_cache/`
- live-search session files under `live_search_sessions/`
- job snapshots under `jobs/`
- local artifacts under `artifacts/`

## Rule

Commit only intentional fixtures and shipped demo data. Do not commit regenerated datasets, caches, sessions, manifests, SQLite files, or other runtime output.
