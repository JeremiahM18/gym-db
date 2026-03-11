import {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import {
  getGym,
  getHealth,
  listGyms,
  nearbyGyms,
  type GymFilters,
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

type ActionLink = {
  label: string;
  href: string;
  tone?: "warm" | "cool" | "ink";
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
const METERS_PER_MILE = 1609.344;
const EARTH_RADIUS_METERS = 6_371_000;

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

function normalizeUrl(value: string | null): string | null {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  return `https://${trimmed}`;
}

function getTagValue(gym: GymOutV2, keys: string[]): string | null {
  const tags = gym.tags ?? {};
  for (const key of keys) {
    const value = tags[key];
    if (value == null) {
      continue;
    }
    const normalized = String(value).trim();
    if (normalized) {
      return normalized;
    }
  }
  return null;
}

function getWebsite(gym: GymOutV2): string | null {
  return normalizeUrl(getTagValue(gym, ["website", "contact:website", "url"]));
}

function getPhone(gym: GymOutV2): string | null {
  return getTagValue(gym, ["phone", "contact:phone"]);
}

function getEmail(gym: GymOutV2): string | null {
  return getTagValue(gym, ["email", "contact:email"]);
}

function getOpeningHours(gym: GymOutV2): string | null {
  return getTagValue(gym, ["opening_hours"]);
}

function getAddress(gym: GymOutV2): string | null {
  const tags = gym.tags ?? {};
  const parts = [
    tags["addr:housenumber"],
    tags["addr:street"],
    tags["addr:city"],
    tags["addr:state"],
    tags["addr:postcode"],
  ]
    .filter((part) => part != null && String(part).trim())
    .map((part) => String(part).trim());
  return parts.length ? parts.join(", ") : null;
}

function getCityState(gym: GymOutV2): string {
  const city = getTagValue(gym, ["addr:city"]);
  const state = getTagValue(gym, ["addr:state"]);
  if (city && state) {
    return `${city}, ${state}`;
  }
  if (city) {
    return city;
  }
  if (state) {
    return state;
  }
  return "City not published";
}

function buildMapsUrl(gym: GymOutV2): string {
  const query = encodeURIComponent(`${gym.lat},${gym.lon} ${gym.name}`);
  return `https://www.google.com/maps/search/?api=1&query=${query}`;
}

function buildOsmUrl(gym: GymOutV2): string {
  return `https://www.openstreetmap.org/?mlat=${gym.lat}&mlon=${gym.lon}#map=18/${gym.lat}/${gym.lon}`;
}

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const originLat = toRadians(lat1);
  const targetLat = toRadians(lat2);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(originLat) * Math.cos(targetLat) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_METERS * c;
}

function formatMilesFromMeters(meters: number): string {
  const miles = meters / METERS_PER_MILE;
  return miles >= 10 ? `${miles.toFixed(0)} mi` : `${miles.toFixed(1)} mi`;
}

function getAmenityChips(gym: GymOutV2): string[] {
  const tags = gym.tags ?? {};
  const amenitySignals: Array<[string, string]> = [
    ["swimming_pool", "Pool"],
    ["sauna", "Sauna"],
    ["shower", "Showers"],
    ["internet_access", "Wi-Fi"],
    ["toilets:wheelchair", "Wheelchair toilets"],
    ["wheelchair", "Wheelchair access"],
    ["opening_hours", "Hours listed"],
    ["website", "Website"],
    ["contact:website", "Website"],
    ["phone", "Phone"],
    ["contact:phone", "Phone"],
  ];

  const chips = new Set<string>();
  for (const [key, label] of amenitySignals) {
    const value = tags[key];
    if (value == null) {
      continue;
    }
    const normalized = String(value).trim().toLowerCase();
    if (!normalized || normalized === "no") {
      continue;
    }
    chips.add(label);
  }

  const specialty = inferString(gym, "specialty", "");
  if (specialty) {
    chips.add(titleCase(specialty));
  }
  if (gym.inference_summary?.premium_score) {
    chips.add(`Premium signal ${gym.inference_summary.premium_score}`);
  }

  return Array.from(chips).slice(0, 8);
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

function ActionPill(props: ActionLink) {
  return (
    <a className={`action-pill ${props.tone ?? "ink"}`} href={props.href} target="_blank" rel="noreferrer">
      {props.label}
    </a>
  );
}

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
    () =>
      catalogResults.filter((gym) => {
        const searchable = [
          gym.name,
          gym.norm_name,
          inferString(gym, "specialty", ""),
          getTagValue(gym, ["addr:city", "addr:street"]) ?? "",
        ]
          .join(" ")
          .toLowerCase();
        return searchable.includes(deferredQuery.trim().toLowerCase());
      }),
    [catalogResults, deferredQuery],
  );

  const visibleNearby = useMemo(
    () =>
      nearbyResults.filter((gym) => {
        const searchable = [
          gym.name,
          gym.norm_name,
          inferString(gym, "specialty", ""),
          getTagValue(gym, ["addr:city", "addr:street"]) ?? "",
        ]
          .join(" ")
          .toLowerCase();
        return searchable.includes(deferredQuery.trim().toLowerCase());
      }),
    [nearbyResults, deferredQuery],
  );

  const activeRows = mode === "catalog" ? visibleCatalog : visibleNearby;

  const averageConfidence = activeRows.length
    ? `${Math.round(
        (activeRows.reduce((sum, gym) => sum + (gym.confidence_score ?? 0), 0) / activeRows.length) *
          100,
      )}%`
    : "n/a";

  const specialtyCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const gym of activeRows) {
      const specialty = inferString(gym, "specialty", "general_fitness");
      counts.set(specialty, (counts.get(specialty) ?? 0) + 1);
    }
    return Array.from(counts.entries()).sort((left, right) => right[1] - left[1]);
  }, [activeRows]);

  const topSpecialty = specialtyCounts.length ? titleCase(specialtyCounts[0][0]) : "n/a";

  const nearbyRadiusLabel = nearbyRadiusMeters ? formatMilesFromMeters(nearbyRadiusMeters) : "n/a";

  const selectedActionLinks = useMemo<ActionLink[]>(() => {
    if (!selectedGym) {
      return [];
    }

    const links: ActionLink[] = [
      { label: "Open in Maps", href: buildMapsUrl(selectedGym), tone: "cool" },
      { label: "Open in OpenStreetMap", href: buildOsmUrl(selectedGym) },
    ];

    const website = getWebsite(selectedGym);
    if (website) {
      links.unshift({ label: "Open website", href: website, tone: "warm" });
    }

    const phone = getPhone(selectedGym);
    if (phone) {
      links.push({ label: "Call gym", href: `tel:${phone.replace(/\s+/g, "")}` });
    }

    const email = getEmail(selectedGym);
    if (email) {
      links.push({ label: "Email gym", href: `mailto:${email}` });
    }

    return links;
  }, [selectedGym]);

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

  const visibleSelectedSpecialty = selectedGym ? titleCase(inferString(selectedGym, "specialty", "general_fitness")) : "n/a";
  const visibleSelectedAddress = selectedGym ? getAddress(selectedGym) : null;
  const visibleSelectedHours = selectedGym ? getOpeningHours(selectedGym) : null;
  const visibleSelectedAmenities = selectedGym ? getAmenityChips(selectedGym) : [];
  const selectedCity = selectedGym ? getCityState(selectedGym) : "City not published";

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
                <small className="field-hint">About {nearbyRadiusLabel}</small>
              </label>
              <div className="controls-actions">
                <button className="secondary-button" type="submit" disabled={loading}>Run nearby search</button>
              </div>
            </form>
          </Panel>

          <Panel
            title="Result Grid"
            subtitle="Deferred local search keeps browsing responsive while live filters stay server-backed."
            accent="Browser Client"
          >
            <div className="toolbar-row">
              <input
                className="search-input"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search loaded results by name, city, street, or specialty"
              />
              <div className="mode-chip-row">
                <button className={mode === "catalog" ? "chip active" : "chip"} type="button" onClick={() => setMode("catalog")}>Catalog</button>
                <button className={mode === "nearby" ? "chip active" : "chip"} type="button" onClick={() => setMode("nearby")} disabled={!nearbyResults.length}>Nearby</button>
              </div>
            </div>

            <div className="result-list">
              {loading ? <div className="empty-state">Loading live backend data...</div> : null}
              {!loading && !activeRows.length ? <div className="empty-state">No gyms matched this query.</div> : null}
              {!loading && mode === "catalog"
                ? visibleCatalog.map((gym) => {
                    const website = getWebsite(gym);
                    const phone = getPhone(gym);
                    return (
                      <button
                        key={gym.id}
                        type="button"
                        className={selectedGymId === gym.id ? "result-card active" : "result-card"}
                        onClick={() => setSelectedGymId(gym.id)}
                      >
                        <div className="result-primary">
                          <div className="result-topline">
                            <strong>{gym.name}</strong>
                            <span className="city-pill">{getCityState(gym)}</span>
                          </div>
                          <span>{titleCase(inferString(gym, "specialty", "general_fitness"))}</span>
                          <p className="result-subcopy">{getAddress(gym) ?? "Coordinates available"}</p>
                          <div className="result-chip-row">
                            {website ? <span className="mini-chip">Website</span> : null}
                            {phone ? <span className="mini-chip">Phone</span> : null}
                            {inferBoolean(gym, "is_24_7") === "Yes" ? <span className="mini-chip">24/7</span> : null}
                          </div>
                        </div>
                        <div className="result-metrics">
                          <span>{formatConfidence(gym.confidence_score)}</span>
                          <span>{titleCase(inferString(gym, "tier", "unknown"))}</span>
                        </div>
                      </button>
                    );
                  })
                : null}
              {!loading && mode === "nearby"
                ? visibleNearby.map((gym) => {
                    const miles = nearbyLat != null && nearbyLon != null
                      ? formatMilesFromMeters(haversineMeters(nearbyLat, nearbyLon, gym.lat, gym.lon))
                      : null;
                    return (
                      <button
                        key={gym.id}
                        type="button"
                        className={selectedGymId === gym.id ? "result-card active" : "result-card"}
                        onClick={() => setSelectedGymId(gym.id)}
                      >
                        <div className="result-primary">
                          <div className="result-topline">
                            <strong>{gym.name}</strong>
                            <span className="city-pill">{getCityState(gym)}</span>
                          </div>
                          <span>{titleCase(inferString(gym, "specialty", "general_fitness"))}</span>
                          <p className="result-subcopy">{getAddress(gym) ?? "Coordinates available"}</p>
                        </div>
                        <div className="result-metrics">
                          <span>{miles ?? "n/a"}</span>
                          <span>{titleCase(inferString(gym, "tier", "unknown"))}</span>
                        </div>
                      </button>
                    );
                  })
                : null}
            </div>
          </Panel>
        </div>

        <Panel
          title="Selected Gym"
          subtitle="Action links, operator facts, public contact surface, and explainable inference from the live v2 contract."
          accent="Explainability"
        >
          {detailLoading ? <div className="empty-state">Loading selected gym...</div> : null}
          {!detailLoading && !selectedGym ? <div className="empty-state">Select a gym to inspect the full public surface.</div> : null}
          {!detailLoading && selectedGym ? (
            <div className="detail-grid">
              <div className="detail-headline">
                <div>
                  <p className="eyebrow">{selectedGym.id}</p>
                  <h3>{selectedGym.name}</h3>
                  <p className="detail-summary">
                    {selectedCity} · {selectedGym.inference_summary?.specialty ?? visibleSelectedSpecialty} · {selectedGym.inference_summary?.tier ?? inferString(selectedGym, "tier", "Unknown")}
                  </p>
                </div>
                <div className="detail-badges">
                  <span>{visibleSelectedSpecialty}</span>
                  <span>{titleCase(inferString(selectedGym, "tier", "unknown"))}</span>
                  <span>{formatConfidence(selectedGym.confidence_score)}</span>
                </div>
              </div>

              <div className="action-rail">
                {selectedActionLinks.map((link) => (
                  <ActionPill key={link.href} {...link} />
                ))}
              </div>

              <div className="detail-facts">
                <StatCard label="Lifter friendly" value={inferBoolean(selectedGym, "lifter_friendly")} tone="cool" />
                <StatCard label="24/7 access" value={inferBoolean(selectedGym, "is_24_7")} tone="warm" />
                <StatCard label="City" value={selectedCity} />
                <StatCard label="Inference engine" value={selectedGym.inference_meta.engine} />
              </div>

              <div className="detail-columns">
                <section className="detail-section">
                  <h4>Visit and Contact</h4>
                  <div className="fact-list">
                    <div className="fact-row">
                      <span>Address</span>
                      <strong>{visibleSelectedAddress ?? "No structured address in source tags"}</strong>
                    </div>
                    <div className="fact-row">
                      <span>Hours</span>
                      <strong>{visibleSelectedHours ?? "Hours not published"}</strong>
                    </div>
                    <div className="fact-row">
                      <span>Phone</span>
                      <strong>{getPhone(selectedGym) ?? "No phone in source tags"}</strong>
                    </div>
                    <div className="fact-row">
                      <span>Email</span>
                      <strong>{getEmail(selectedGym) ?? "No email in source tags"}</strong>
                    </div>
                  </div>
                </section>

                <section className="detail-section">
                  <h4>Signals and Amenities</h4>
                  <div className="tag-cloud">
                    {visibleSelectedAmenities.length
                      ? visibleSelectedAmenities.map((chip) => <span key={chip} className="tag-pill">{chip}</span>)
                      : <p className="detail-copy">No prominent amenity tags were published for this gym.</p>}
                  </div>
                  <p className="detail-copy">
                    OSM refs: {selectedGym.osm_refs.length} linked source record{selectedGym.osm_refs.length === 1 ? "" : "s"}.
                  </p>
                </section>
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

