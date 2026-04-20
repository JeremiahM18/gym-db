# Backend Data

This directory intentionally mixes a few small tracked fixtures with ignored runtime output.

Tracked in git:
- `registry.json`: checked-in dataset registry configuration
- `gyms_nashville.json`: the shipped Nashville default dataset used for demos and first-load product state
- `registry_test.json`: tiny test registry fixture
- `gyms_test.json`: tiny test dataset fixture
- `.gitkeep`: preserves the directory in fresh clones
- `README.md`: explains the fixture/runtime boundary

Ignored from git:
- local or regenerated datasets such as `gyms_raw.json`
- generated dataset sidecars such as `*.sqlite3` and temporary lock files
- generated dataset manifests such as `*.manifest.json`
- warmed live-search cache files under `live_search_cache/`
- runtime job snapshots under `jobs/`
- operational artifacts under `artifacts/`, including local TomTom coverage audit outputs

The rule is simple: tiny fixtures and the intentionally shipped default Nashville dataset may be committed; local regenerated runtime data should not be.
