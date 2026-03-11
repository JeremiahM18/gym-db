# GymDB Frontend

This frontend is a thin exploratory client for the GymDB backend, not the primary product surface.

## Current Role

The frontend exists to:
- exercise the versioned API from a browser client
- validate generated OpenAPI client usage
- provide a place for future product-facing UI work without coupling it to backend architecture decisions

The backend remains the authoritative focus of the project.

## Commands

- `npm run dev`
  Start the Vite development server.

- `npm run lint`
  Run frontend linting.

- `npm run build`
  Build the frontend bundle.

- `npm run generate:api`
  Regenerate the typed API client from the backend OpenAPI document.

## Notes

- `src/api/` is generated client code and is excluded from lint noise.
- The current UI is intentionally minimal while the backend architecture is still evolving.
