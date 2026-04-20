import {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  defaultFilters,
  defaultLiveSearch,
  type ActionLink,
  type BrowserGym,
  type FiltersState,
  type LiveSearchState,
  type Mode,
} from "./features/gym-browser/types";
import { GeoCanvasPanel } from "./features/gym-browser/GeoCanvasPanel";
import { HeroSection } from "./features/gym-browser/HeroSection";
import { QueryControlsPanel } from "./features/gym-browser/QueryControlsPanel";
import { ResultsPanel } from "./features/gym-browser/ResultsPanel";
import { SelectedGymPanel } from "./features/gym-browser/SelectedGymPanel";
import { StatusStrip } from "./features/gym-browser/StatusStrip";
import {
  buildGymFilters,
  buildLiveBrowserGym,
  buildPublishedBrowserGym,
  buildSelectedActionLinks,
  filterGymsByQuery,
  formatMilesValue,
  getAverageConfidence,
  getTopSpecialty,
  milesToMeters,
  parseNumber,
} from "./features/gym-browser/utils";
import {
  getGym,
  getHealth,
  listGyms,
  liveSearchGyms,
  toUserFacingErrorMessage,
  type HealthSnapshot,
} from "./lib/api";

type LiveOrigin = {
  lat: number;
  lon: number;
  label: string;
} | null;

export function App() {
  const [mode, setMode] = useState<Mode>("published");
  const [filters, setFilters] = useState<FiltersState>(defaultFilters);
  const [liveSearch, setLiveSearch] = useState<LiveSearchState>(defaultLiveSearch);
  const [query, setQuery] = useState("");
  const [publishedResults, setPublishedResults] = useState<BrowserGym[]>([]);
  const [liveResults, setLiveResults] = useState<BrowserGym[]>([]);
  const [selectedGymId, setSelectedGymId] = useState<string | null>(null);
  const [selectedGym, setSelectedGym] = useState<BrowserGym | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [liveOrigin, setLiveOrigin] = useState<LiveOrigin>(null);

  const deferredQuery = useDeferredValue(query);
  const liveRadiusMiles = parseNumber(liveSearch.radiusMiles);
  const nextSuggestedRadiusMiles = Math.min(
    100,
    Math.max(10, Math.ceil((liveRadiusMiles ?? 10) * 2)),
  );

  useEffect(() => {
    const controller = new AbortController();

    async function bootstrap() {
      try {
        const [healthSnapshot, gyms] = await Promise.all([
          getHealth(controller.signal),
          listGyms(buildGymFilters(defaultFilters), controller.signal),
        ]);

        startTransition(() => {
          const mapped = gyms.results.map(buildPublishedBrowserGym);
          setHealth(healthSnapshot);
          setPublishedResults(mapped);
          setSelectedGymId(mapped[0]?.id ?? null);
        });
      } catch (loadError) {
        if (controller.signal.aborted) {
          return;
        }
        setError(
          toUserFacingErrorMessage(loadError, "We couldn't load gyms right now."),
        );
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
    if (mode === "live") {
      const liveGym = liveResults.find((gym) => gym.id === selectedGymId) ?? null;
      setSelectedGym(liveGym);
      setDetailLoading(false);
      return;
    }

    if (!selectedGymId) {
      setSelectedGym(null);
      return;
    }

    const selectedPublishedSummary =
      publishedResults.find((gym) => gym.id === selectedGymId) ?? null;
    if (!selectedPublishedSummary?.rawPublishedGymId) {
      setSelectedGym(selectedPublishedSummary);
      return;
    }

    const controller = new AbortController();
    setDetailLoading(true);

    void getGym(
      selectedPublishedSummary.rawPublishedGymId,
      filters.region || undefined,
      controller.signal,
    )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        startTransition(() => {
          setSelectedGym(buildPublishedBrowserGym(response.gym));
        });
      })
      .catch((detailError) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(
          toUserFacingErrorMessage(detailError, "We couldn't load gym details right now."),
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [filters.region, mode, publishedResults, selectedGymId, liveResults]);

  const visiblePublished = useMemo(
    () => filterGymsByQuery(publishedResults, deferredQuery),
    [publishedResults, deferredQuery],
  );

  const visibleLive = useMemo(
    () => filterGymsByQuery(liveResults, deferredQuery),
    [liveResults, deferredQuery],
  );

  const activeRows = mode === "published" ? visiblePublished : visibleLive;
  const averageConfidence = useMemo(
    () => getAverageConfidence(activeRows),
    [activeRows],
  );
  const topSpecialty = useMemo(() => getTopSpecialty(activeRows), [activeRows]);

  const liveRadiusLabel = liveRadiusMiles != null
    ? formatMilesValue(liveRadiusMiles)
    : "n/a";
  const livePlaceLabel =
    liveSearch.resolvedLabel || liveOrigin?.label || liveSearch.placeQuery.trim() || "your chosen place";
  const liveSearchSummary =
    mode === "live"
      ? `${liveSearch.query.trim() || "gym"} within ${liveRadiusLabel} of ${livePlaceLabel}`
      : `Use Live Search to find gyms within a chosen radius of any place.`;
  const selectedActionLinks = useMemo<ActionLink[]>(
    () => buildSelectedActionLinks(selectedGym),
    [selectedGym],
  );

  async function loadPublishedCatalog(nextFilters: FiltersState = filters) {
    setLoading(true);
    setError(null);

    try {
      const response = await listGyms(buildGymFilters(nextFilters));
      const mapped = response.results.map(buildPublishedBrowserGym);
      startTransition(() => {
        setMode("published");
        setPublishedResults(mapped);
        setSelectedGymId(mapped[0]?.id ?? null);
      });
    } catch (loadError) {
      setError(
        toUserFacingErrorMessage(loadError, "We couldn't load curated gyms right now."),
      );
    } finally {
      setLoading(false);
    }
  }

  async function runLiveSearch(nextLiveSearch: LiveSearchState = liveSearch) {
    setLoading(true);
    setError(null);

    const placeQuery = nextLiveSearch.placeQuery.trim();
    const searchQuery = nextLiveSearch.query.trim() || "gym";
    const nextRadiusMiles = parseNumber(nextLiveSearch.radiusMiles);
    const nextRadiusMeters =
      nextRadiusMiles != null ? milesToMeters(nextRadiusMiles) : undefined;

    if (!placeQuery) {
      setError(
        "Enter a city, neighborhood, landmark, or ZIP code to search nearby gyms.",
      );
      setLoading(false);
      return;
    }

    if (
      nextRadiusMiles == null
      || nextRadiusMeters == null
      || nextRadiusMiles <= 0
    ) {
      setError("Choose a radius greater than zero miles.");
      setLoading(false);
      return;
    }

    try {
      const response = await liveSearchGyms(placeQuery, searchQuery, nextRadiusMeters);
      const mapped = response.results
        .map(buildLiveBrowserGym)
        .sort((left, right) => {
          if (left.distanceM == null && right.distanceM == null) {
            return left.name.localeCompare(right.name);
          }
          if (left.distanceM == null) {
            return 1;
          }
          if (right.distanceM == null) {
            return -1;
          }
          return left.distanceM - right.distanceM;
        });
      startTransition(() => {
        setMode("live");
        setLiveResults(mapped);
        setSelectedGymId(mapped[0]?.id ?? null);
        setLiveSearch((current) => ({
          ...current,
          ...nextLiveSearch,
          query: response.query,
          resolvedLabel: response.origin.address || response.origin.name,
        }));
        setLiveOrigin({
          lat: response.origin.lat,
          lon: response.origin.lon,
          label: response.origin.address || response.origin.name,
        });
      });
    } catch (loadError) {
      setError(
        toUserFacingErrorMessage(
          loadError,
          "We couldn't run that nearby search right now.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  async function handlePublishedSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadPublishedCatalog(filters);
  }

  async function handleLiveSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runLiveSearch(liveSearch);
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <main className="app-frame">
        <HeroSection
          mode={mode}
          activeRowCount={activeRows.length}
          averageConfidence={averageConfidence}
          liveRadiusLabel={liveRadiusLabel}
          livePlaceLabel={livePlaceLabel}
          liveSearchSummary={liveSearchSummary}
          topSpecialty={topSpecialty}
          selectedActionLinks={selectedActionLinks}
        />

        <StatusStrip
          health={health}
        />

        {error ? (
          <div className="error-banner">
            <div>
              <strong>Something needs attention</strong>
              <p>{error}</p>
            </div>
            <div className="error-banner-actions">
              <button
                type="button"
                className="chip active"
                onClick={() => {
                  if (mode === "live") {
                    void runLiveSearch();
                    return;
                  }
                  void loadPublishedCatalog();
                }}
              >
                Try again
              </button>
              <button
                type="button"
                className="chip"
                onClick={() => setError(null)}
              >
                Dismiss
              </button>
            </div>
          </div>
        ) : null}

        <div className="discovery-shell">
          <aside className="search-rail">
            <QueryControlsPanel
              mode={mode}
              filters={filters}
              liveSearch={liveSearch}
              loading={loading}
              liveRadiusLabel={liveRadiusLabel}
              liveSearchSummary={liveSearchSummary}
              onModeChange={(nextMode) => {
                setMode(nextMode);
                setSelectedGymId(
                  nextMode === "published"
                    ? visiblePublished[0]?.id ?? null
                    : visibleLive[0]?.id ?? null,
                );
              }}
              onPublishedSubmit={handlePublishedSubmit}
              onLiveSubmit={handleLiveSubmit}
              setFilters={setFilters}
              setLiveSearch={setLiveSearch}
            />
          </aside>

          <section className="results-rail">
            <ResultsPanel
              query={query}
              mode={mode}
              loading={loading}
              selectedGymId={selectedGymId}
              visiblePublished={visiblePublished}
              visibleLive={visibleLive}
              livePlaceLabel={livePlaceLabel}
              liveRadiusLabel={liveRadiusLabel}
              liveSearchSummary={liveSearchSummary}
              onQueryChange={setQuery}
              onExpandLiveRadius={() =>
                setLiveSearch((current) => ({
                  ...current,
                  radiusMiles: String(nextSuggestedRadiusMiles),
                }))
              }
              onSwitchToLiveMode={() => setMode("live")}
              onSelectGym={setSelectedGymId}
            />
          </section>

          <section className="detail-rail">
            <SelectedGymPanel
              detailLoading={detailLoading}
              mode={mode}
              selectedGym={selectedGym}
              selectedActionLinks={selectedActionLinks}
            />
            <GeoCanvasPanel
              mode={mode}
              gyms={activeRows}
              selectedGymId={selectedGymId}
              onSelectGym={setSelectedGymId}
              nearbyLat={mode === "live" ? liveOrigin?.lat : undefined}
              nearbyLon={mode === "live" ? liveOrigin?.lon : undefined}
              livePlaceLabel={mode === "live" ? livePlaceLabel : undefined}
              liveRadiusLabel={mode === "live" ? liveRadiusLabel : undefined}
            />
          </section>
        </div>
      </main>
    </div>
  );
}
