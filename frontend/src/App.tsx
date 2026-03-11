import {
  startTransition,
  useDeferredValue,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";

import {
  getGym,
  getHealth,
  listGyms,
  nearbyGyms,
  type GymFilters,
  type GymNearbyOutV2,
  type GymOutV2,
  type HealthSnapshot,
} from "./lib/api";

type Mode = "catalog" | "nearby";
type ToggleChoice = "any" | "yes" | "no";

type FiltersState = {
  region: string;
  minConf: string;
  tier: string;
  specialty: string;
  lifterFriendly: ToggleChoice;
  is247: ToggleChoice;
  limit: string;
};

type NearbyState = {
  lat: string;
  lon: string;
  radiusM: string;
};

const specialtyOptions = [
  "general_fitness",
  "crossfit",
  "powerlifting",
  "olympic_weightlifting",
  "bodybuilding",
  "boxing",
  "martial_arts",
  "yoga",
  "climbing",
] as const;

const tierOptions = ["basic", "mid", "premium"] as const;

const defaultFilters: FiltersState = {
  region: "",
  minConf: "0.7",
  tier: "",
  specialty: "",
  lifterFriendly: "any",
  is247: "any",
  limit: "100",
};

const defaultNearby: NearbyState = {
  lat: "36.1627",
  lon: "-86.7816",
  radiusM: "2500",
};

function choiceToBoolean(choice: ToggleChoice): boolean | undefined {
  if (choice === "yes") {
    return true;
  }
  if (choice === "no") {
    return false;
  }
  return undefined;
}

function parseNumber(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function buildGymFilters(filters: FiltersState): GymFilters {
  return {
    region: filters.region || undefined,
    minConf: parseNumber(filters.minConf),
    tier: filters.tier || undefined,
    specialty: filters.specialty || undefined,
    lifterFriendly: choiceToBoolean(filters.lifterFriendly),
    is247: choiceToBoolean(filters.is247),
    limit: parseNumber(filters.limit) ?? 100,
    offset: 0,
  };
}

function formatConfidence(value: number | null | undefined): string {
  if (value == null) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function titleCase(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function inferString(gym: GymOutV2, key: string, fallback = "Unknown"): string {
  const result = gym.inference[key];
  return result ? String(result.value) : fallback;
}

function inferBoolean(gym: GymOutV2, key: string): string {
  const result = gym.inference[key];
  if (!result) {
    return "Unknown";
  }
  return result.value ? "Yes" : "No";
}

function StatCard(props: { label: string; value: string; tone?: "warm" | "cool" | "ink" }) {
  return (
    <div className={`stat-card ${props.tone ?? "ink"}`}>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </div>
  );
}

function Panel(props: { title: string; subtitle?: string; children: ReactNode; accent?: string }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">{props.accent ?? "Operator Surface"}</p>
          <h2>{props.title}</h2>
        </div>
        {props.subtitle ? <p className="panel-subtitle">{props.subtitle}</p> : null}
      </div>
      {props.children}
    </section>
  );
}

export function App() {
  const [mode, setMode] = useState<Mode>("catalog");
  const [filters, setFilters] = useState<FiltersState>(defaultFilters);
  const [nearby, setNearby] = useState<NearbyState>(defaultNearby);
  const [query, setQuery] = useState("");
  const [catalogResults, setCatalogResults] = useState<GymOutV2[]>([]);
  const [nearbyResults, setNearbyResults] = useState<GymNearbyOutV2[]>([]);
  const [selectedGymId, setSelectedGymId] = useState<string | null>(null);
  const [selectedGym, setSelectedGym] = useState<GymOutV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);

  const deferredQuery = useDeferredValue(query);

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

  const visibleCatalog = catalogResults.filter((gym) => {
    const searchable = `${gym.name} ${gym.norm_name} ${inferString(gym, "specialty", "")}`.toLowerCase();
    return searchable.includes(deferredQuery.trim().toLowerCase());
  });

  const averageConfidence = visibleCatalog.length
    ? `${Math.round(
        (visibleCatalog.reduce((sum, gym) => sum + (gym.confidence_score ?? 0), 0) /
          visibleCatalog.length) *
          100,
      )}%`
    : "n/a";

  const topSpecialty = visibleCatalog.length
    ? titleCase(inferString(visibleCatalog[0], "specialty", "general_fitness"))
    : "n/a";

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

    const lat = parseNumber(nearby.lat);
    const lon = parseNumber(nearby.lon);
    const radiusM = parseNumber(nearby.radiusM);

    if (lat == null || lon == null || radiusM == null) {
      setError("Nearby search requires numeric latitude, longitude, and radius.");
      setLoading(false);
      return;
    }

    try {
      const response = await nearbyGyms({
        ...buildGymFilters(filters),
        lat,
        lon,
        radiusM,
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

  const activeRows = mode === "catalog" ? visibleCatalog : nearbyResults;

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <main className="app-frame">
        <section className="hero">
          <div>
            <p className="eyebrow">GymDB Operator Console</p>
            <h1>Enterprise-grade gym intelligence, exposed through a frontend worth showing off.</h1>
            <p className="hero-copy">
              Browse published artifacts, inspect explainable inference, and run nearby search
              against the same backend contracts you built for production.
            </p>
          </div>
          <div className="hero-grid">
            <StatCard label="Mode" value={mode === "catalog" ? "Catalog" : "Nearby"} tone="warm" />
            <StatCard label="Visible gyms" value={String(activeRows.length)} tone="cool" />
            <StatCard label="Avg confidence" value={averageConfidence} />
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
          <div className="status-pill neutral">API base: {import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}</div>
        </section>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="workspace-grid">
          <Panel
            title="Query Controls"
            subtitle="Run catalog filters or nearby search against the live backend."
            accent="Read Surface"
          >
            <form className="controls-grid" onSubmit={handleCatalogSubmit}>
              <label>
                <span>Region</span>
                <input value={filters.region} onChange={(event) => setFilters((current) => ({ ...current, region: event.target.value }))} placeholder="default region" />
              </label>
              <label>
                <span>Min confidence</span>
                <input value={filters.minConf} onChange={(event) => setFilters((current) => ({ ...current, minConf: event.target.value }))} inputMode="decimal" />
              </label>
              <label>
                <span>Tier</span>
                <select value={filters.tier} onChange={(event) => setFilters((current) => ({ ...current, tier: event.target.value }))}>
                  <option value="">Any</option>
                  {tierOptions.map((tier) => (
                    <option key={tier} value={tier}>{titleCase(tier)}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Specialty</span>
                <select value={filters.specialty} onChange={(event) => setFilters((current) => ({ ...current, specialty: event.target.value }))}>
                  <option value="">Any</option>
                  {specialtyOptions.map((specialty) => (
                    <option key={specialty} value={specialty}>{titleCase(specialty)}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Lifter friendly</span>
                <select value={filters.lifterFriendly} onChange={(event) => setFilters((current) => ({ ...current, lifterFriendly: event.target.value as ToggleChoice }))}>
                  <option value="any">Any</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
              <label>
                <span>24/7</span>
                <select value={filters.is247} onChange={(event) => setFilters((current) => ({ ...current, is247: event.target.value as ToggleChoice }))}>
                  <option value="any">Any</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
              <label>
                <span>Result limit</span>
                <input value={filters.limit} onChange={(event) => setFilters((current) => ({ ...current, limit: event.target.value }))} inputMode="numeric" />
              </label>
              <div className="controls-actions">
                <button className="primary-button" type="submit" disabled={loading}>Refresh catalog</button>
              </div>
            </form>

            <form className="controls-grid nearby-grid" onSubmit={handleNearbySubmit}>
              <label>
                <span>Latitude</span>
                <input value={nearby.lat} onChange={(event) => setNearby((current) => ({ ...current, lat: event.target.value }))} inputMode="decimal" />
              </label>
              <label>
                <span>Longitude</span>
                <input value={nearby.lon} onChange={(event) => setNearby((current) => ({ ...current, lon: event.target.value }))} inputMode="decimal" />
              </label>
              <label>
                <span>Radius (meters)</span>
                <input value={nearby.radiusM} onChange={(event) => setNearby((current) => ({ ...current, radiusM: event.target.value }))} inputMode="numeric" />
              </label>
              <div className="controls-actions">
                <button className="secondary-button" type="submit" disabled={loading}>Run nearby search</button>
              </div>
            </form>
          </Panel>

          <Panel
            title="Result Grid"
            subtitle="Client-side text query is deferred so browsing stays responsive while the live filters stay server-backed."
            accent="Browser Client"
          >
            <div className="toolbar-row">
              <input
                className="search-input"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search loaded results by name or specialty"
              />
              <div className="mode-chip-row">
                <button className={mode === "catalog" ? "chip active" : "chip"} type="button" onClick={() => setMode("catalog")}>Catalog</button>
                <button className={mode === "nearby" ? "chip active" : "chip"} type="button" onClick={() => setMode("nearby")} disabled={!nearbyResults.length}>Nearby</button>
              </div>
            </div>

            <div className="result-list">
              {loading ? <div className="empty-state">Loading live backend data…</div> : null}
              {!loading && !activeRows.length ? <div className="empty-state">No gyms matched this query.</div> : null}
              {!loading && mode === "catalog"
                ? visibleCatalog.map((gym) => (
                    <button
                      key={gym.id}
                      type="button"
                      className={selectedGymId === gym.id ? "result-card active" : "result-card"}
                      onClick={() => setSelectedGymId(gym.id)}
                    >
                      <div>
                        <strong>{gym.name}</strong>
                        <span>{titleCase(inferString(gym, "specialty", "general_fitness"))}</span>
                      </div>
                      <div className="result-metrics">
                        <span>{formatConfidence(gym.confidence_score)}</span>
                        <span>{titleCase(inferString(gym, "tier", "unknown"))}</span>
                      </div>
                    </button>
                  ))
                : null}
              {!loading && mode === "nearby"
                ? nearbyResults.map((gym) => (
                    <button
                      key={gym.id}
                      type="button"
                      className={selectedGymId === gym.id ? "result-card active" : "result-card"}
                      onClick={() => setSelectedGymId(gym.id)}
                    >
                      <div>
                        <strong>{gym.name}</strong>
                        <span>{gym.lat.toFixed(4)}, {gym.lon.toFixed(4)}</span>
                      </div>
                      <div className="result-metrics">
                        <span>{Math.round(gym.distance_m)} m</span>
                      </div>
                    </button>
                  ))
                : null}
            </div>
          </Panel>
        </div>

        <Panel
          title="Gym Detail"
          subtitle="Structured inference, confidence, and reasoning from the live v2 contract."
          accent="Explainability"
        >
          {detailLoading ? <div className="empty-state">Loading selected gym…</div> : null}
          {!detailLoading && !selectedGym ? <div className="empty-state">Select a gym to inspect inference output.</div> : null}
          {!detailLoading && selectedGym ? (
            <div className="detail-grid">
              <div className="detail-headline">
                <div>
                  <p className="eyebrow">{selectedGym.id}</p>
                  <h3>{selectedGym.name}</h3>
                </div>
                <div className="detail-badges">
                  <span>{titleCase(inferString(selectedGym, "specialty", "general_fitness"))}</span>
                  <span>{titleCase(inferString(selectedGym, "tier", "unknown"))}</span>
                  <span>{formatConfidence(selectedGym.confidence_score)}</span>
                </div>
              </div>

              <div className="detail-facts">
                <StatCard label="Lifter friendly" value={inferBoolean(selectedGym, "lifter_friendly")} tone="cool" />
                <StatCard label="24/7 access" value={inferBoolean(selectedGym, "is_24_7")} tone="warm" />
                <StatCard label="Coordinates" value={`${selectedGym.lat.toFixed(4)}, ${selectedGym.lon.toFixed(4)}`} />
                <StatCard label="Inference engine" value={selectedGym.inference_meta.engine} />
              </div>

              <div className="inference-table">
                {Object.entries(selectedGym.inference).map(([key, value]) => (
                  <article key={key} className="inference-row">
                    <div>
                      <p className="inference-key">{titleCase(key)}</p>
                      <strong>{String(value.value)}</strong>
                    </div>
                    <div>
                      <p className="inference-meta">Confidence {formatConfidence(value.confidence ?? null)}</p>
                      <p className="inference-reasons">{value.reasons.join(" • ") || "No explicit reasons"}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
        </Panel>
      </main>
    </div>
  );
}
