# Backend Data

This directory intentionally mixes a few small tracked fixtures with ignored runtime output.

Tracked in git:
- `registry.json`: checked-in dataset registry configuration
- `registry_test.json`: tiny test registry fixture
- `gyms_test.json`: tiny test dataset fixture
- `.gitkeep`: preserves the directory in fresh clones

Ignored from git:
- generated ingest outputs such as `gyms_raw.json`
- runtime job snapshots under `jobs/`
- operational artifacts under `artifacts/`

The rule is simple: tiny deterministic fixtures may be committed; runtime or regenerated data should not be.
