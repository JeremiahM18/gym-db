import {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from "react";

import { ActionPill } from "./components/ActionPill";
import { GeoMap } from "./components/GeoMap";
import { StatCard } from "./components/StatCard";
import {
  defaultFilters,
  defaultNearby,
  type ActionLink,
  type FiltersState,
  type Mode,
  type NearbyState,
} from "./features/gym-browser/types";
import { QueryControlsPanel } from "./features/gym-browser/QueryControlsPanel";
import { ResultsPanel } from "./features/gym-browser/ResultsPanel";
import { SelectedGymPanel } from "./features/gym-browser/SelectedGymPanel";
import {
  buildGymFilters,
  buildSelectedActionLinks,
  filterGymsByQuery,
  formatMilesFromMeters,
  getAverageConfidence,
  getTopSpecialty,
  parseNumber,
} from "./features/gym-browser/utils";
import {
  getGym,
  getHealth,
  listGyms,
  nearbyGyms,
  type GymOutV2,
  type HealthSnapshot,
} from "./lib/api";

export function App() {
  const [mode, setMode] = useState<Mode>("catalog");
  const [filters, setFilters] = useState<FiltersState>(defaultFilters);
  const [nearby, setNearby] = useState<NearbyState>(defaultNearby);
  const [query, setQuery] = useState("");
  const [catalogResults, setCatalogResults] = useState<GymOutV2[]>([]);
  const [nearbyResults, setNearbyResults] = useState<GymOutV2[]>([]);
  const [selectedGymId, setSelectedGymId] = useState<string | null>(null);
  const [selectedGym, setSelectedGym] = useState<GymOutV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);

  const deferredQuery = useDeferredValue(query);
  const nearbyLat = parseNumber(nearby.lat);
  const nearbyLon = parseNumber(nearby.lon);
  const nearbyRadiusMeters = parseNumber(nearby.radiusM);

  useEffect(() => {
    const controller = new AbortController();

    async function bootstrap() {
      try {
        const [healthSnapshot, gyms] = await Promise.all([
          getHealth(controller.signal),
          listGyms(buildGymFilters(defaultFilters), controller.signal),
        ]);

        startTransition(() => {
          setHealth(healthSnapshot);
          setCatalogResults(gyms.results);
          setSelectedGymId(gyms.results[0]?.id ?? null);
        });
      } catch (loadError) {
        if (controller.signal.aborted) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load GymDB.");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void bootstrap();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedGymId) {
      setSelectedGym(null);
      return;
    }

    const controller = new AbortController();
    setDetailLoading(true);

    void getGym(selectedGymId, filters.region || undefined, controller.signal)
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        startTransition(() => {
          setSelectedGym(response.gym);
        });
      })
      .catch((detailError) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(detailError instanceof Error ? detailError.message : "Failed to load gym detail.");
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [filters.region, selectedGymId]);

  const visibleCatalog = useMemo(
    () => filterGymsByQuery(catalogResults, deferredQuery),
    [catalogResults, deferredQuery],
  );

  const visibleNearby = useMemo(
    () => filterGymsByQuery(nearbyResults, deferredQuery),
    [nearbyResults, deferredQuery],
  );

  const activeRows = mode === "catalog" ? visibleCatalog : visibleNearby;
  const averageConfidence = useMemo(() => getAverageConfidence(activeRows), [activeRows]);
  const topSpecialty = useMemo(() => getTopSpecialty(activeRows), [activeRows]);

  const nearbyRadiusLabel = nearbyRadiusMeters ? formatMilesFromMeters(nearbyRadiusMeters) : "n/a";
  const selectedActionLinks = useMemo<ActionLink[]>(
    () => buildSelectedActionLinks(selectedGym),
    [selectedGym],
  );

  async function handleCatalogSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await listGyms(buildGymFilters(filters));
      startTransition(() => {
        setMode("catalog");
        setCatalogResults(response.results);
        setNearbyResults([]);
        setSelectedGymId(response.results[0]?.id ?? null);
      });
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to query gyms.");
    } finally {
      setLoading(false);
    }
  }

  async function handleNearbySubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    if (nearbyLat == null || nearbyLon == null || nearbyRadiusMeters == null) {
      setError("Nearby search requires numeric latitude, longitude, and radius.");
      setLoading(false);
      return;
    }

    try {
      const response = await nearbyGyms({
        ...buildGymFilters(filters),
        lat: nearbyLat,
        lon: nearbyLon,
        radiusM: nearbyRadiusMeters,
      });
      startTransition(() => {
        setMode("nearby");
        setNearbyResults(response.results);
        setSelectedGymId(response.results[0]?.id ?? null);
      });
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to run nearby search.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <main className="app-frame">
        <section className="hero">
          <div>
            <p className="eyebrow">GymDB Browser Client</p>
            <h1>Find gyms, inspect inference, and jump straight into places you can actually visit.</h1>
            <p className="hero-copy">
              Browse the live catalog, filter by specialty and quality, run nearby search without a
              database-only dependency, and jump out to maps or official gym sites in one flow.
            </p>
            <div className="hero-actions">
              {selectedActionLinks.slice(0, 3).map((link) => (
                <ActionPill key={link.href} {...link} />
              ))}
            </div>
          </div>
          <div className="hero-grid">
            <StatCard label="Mode" value={mode === "catalog" ? "Catalog" : "Nearby"} tone="warm" />
            <StatCard label="Visible gyms" value={String(activeRows.length)} tone="cool" />
            <StatCard label="Avg confidence" value={averageConfidence} />
            <StatCard label="Search radius" value={mode === "nearby" ? nearbyRadiusLabel : "Catalog"} />
            <StatCard label="Lead specialty" value={topSpecialty} />
          </div>
        </section>

        <section className="status-strip">
          <div className={`status-pill ${health?.live ? "healthy" : "degraded"}`}>
            <span className="status-dot" />
            API live: {health?.live ? "yes" : "unknown"}
          </div>
          <div className={`status-pill ${health?.ready ? "healthy" : "degraded"}`}>
            <span className="status-dot" />
            Backend ready: {health?.ready ? "yes" : "check readiness"}
          </div>
          <div className="status-pill neutral">
            API base: {import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}
          </div>
        </section>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="workspace-grid">
          <QueryControlsPanel
            filters={filters}
            nearby={nearby}
            loading={loading}
            nearbyRadiusLabel={nearbyRadiusLabel}
            onCatalogSubmit={handleCatalogSubmit}
            onNearbySubmit={handleNearbySubmit}
            setFilters={setFilters}
            setNearby={setNearby}
          />

          <ResultsPanel
            query={query}
            mode={mode}
            loading={loading}
            selectedGymId={selectedGymId}
            visibleCatalog={visibleCatalog}
            visibleNearby={visibleNearby}
            nearbyLat={nearbyLat}
            nearbyLon={nearbyLon}
            onQueryChange={setQuery}
            onModeChange={setMode}
            onSelectGym={setSelectedGymId}
          />
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Spatial Surface</p>
              <h2>Geo Canvas</h2>
            </div>
            <p className="panel-subtitle">
              A live coordinate projection of the current result set with selectable gym pins.
            </p>
          </div>
          <GeoMap
            gyms={activeRows}
            selectedGymId={selectedGymId}
            onSelect={setSelectedGymId}
            nearbyLat={mode === "nearby" ? nearbyLat : undefined}
            nearbyLon={mode === "nearby" ? nearbyLon : undefined}
          />
        </div>

        <SelectedGymPanel
          detailLoading={detailLoading}
          selectedGym={selectedGym}
          selectedActionLinks={selectedActionLinks}
        />
      </main>
    </div>
  );
}

