import {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { Dispatch, SetStateAction } from "react";

import {
  defaultFilters,
  defaultLiveSearch,
  type ActionLink,
  type BrowserGym,
  type FiltersState,
  type LiveSearchSessionState,
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
  milesToMeters,
  parseNumber,
} from "./features/gym-browser/utils";
import {
  getGym,
  getHealth,
  getLiveSearchSession,
  listGyms,
  liveSearchGyms,
  toUserFacingErrorMessage,
  type HealthSnapshot,
  type LiveGymSearchResponseV2,
} from "./lib/api";

type LiveOrigin = {
  lat: number;
  lon: number;
  label: string;
} | null;

type LiveResponseOptions = {
  activateMode: boolean;
  syncControls: boolean;
  updateSelection: boolean;
  preferredSelectedGymId?: string | null;
};

type LiveResponseSetters = {
  setMode: Dispatch<SetStateAction<Mode>>;
  setLiveResults: Dispatch<SetStateAction<BrowserGym[]>>;
  setSelectedGymId: Dispatch<SetStateAction<string | null>>;
  setLiveSearch: Dispatch<SetStateAction<LiveSearchState>>;
  setLiveOrigin: Dispatch<SetStateAction<LiveOrigin>>;
  setLiveSession: Dispatch<SetStateAction<LiveSearchSessionState | null>>;
};

function buildLiveSessionState(
  response: LiveGymSearchResponseV2,
): LiveSearchSessionState {
  return {
    searchId: response.search_id,
    status: response.status,
    enrichmentStatus: response.enrichment_status,
    revision: response.revision,
    updatedAt: response.updated_at,
    expiresAt: response.expires_at,
    pollAfterMs: response.poll_after_ms ?? null,
  };
}

function mapLiveResponse(response: LiveGymSearchResponseV2): BrowserGym[] {
  return response.results
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
}

function applyLiveResponse(
  response: LiveGymSearchResponseV2,
  nextLiveSearch: LiveSearchState,
  options: LiveResponseOptions,
  setters: LiveResponseSetters,
) {
  const mappedLive = mapLiveResponse(response);
  const resolvedLabel = response.origin.address || response.origin.name;

  startTransition(() => {
    if (options.activateMode) {
      setters.setMode("live");
    }
    setters.setLiveResults(mappedLive);
    if (options.updateSelection) {
      setters.setSelectedGymId((current) => {
        const preferredSelectedGymId = options.preferredSelectedGymId ?? current;
        if (
          preferredSelectedGymId
          && mappedLive.some((gym) => gym.id === preferredSelectedGymId)
        ) {
          return preferredSelectedGymId;
        }
        return mappedLive[0]?.id ?? null;
      });
    }
    if (options.syncControls) {
      setters.setLiveSearch((current) => ({
        ...current,
        ...nextLiveSearch,
        query: response.query,
        resolvedLabel,
      }));
    } else {
      setters.setLiveSearch((current) => ({
        ...current,
        resolvedLabel,
      }));
    }
    setters.setLiveOrigin({
      lat: response.origin.lat,
      lon: response.origin.lon,
      label: resolvedLabel,
    });
    setters.setLiveSession(buildLiveSessionState(response));
  });
}

export function App() {
  const [mode, setMode] = useState<Mode>("live");
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
  const [liveSession, setLiveSession] = useState<LiveSearchSessionState | null>(
    null,
  );

  const deferredQuery = useDeferredValue(query);
  const liveRadiusMiles = parseNumber(liveSearch.radiusMiles);
  const nextSuggestedRadiusMiles = Math.min(
    100,
    Math.max(10, Math.ceil((liveRadiusMiles ?? 10) * 2)),
  );

  useEffect(() => {
    const controller = new AbortController();

    async function bootstrap() {
      const initialRadiusMiles = parseNumber(defaultLiveSearch.radiusMiles);
      const initialRadiusMeters =
        initialRadiusMiles != null ? milesToMeters(initialRadiusMiles) : undefined;

      try {
        const [healthResult, publishedResult, liveResult] = await Promise.allSettled([
          getHealth(controller.signal),
          listGyms(buildGymFilters(defaultFilters), controller.signal),
          initialRadiusMeters != null
            ? liveSearchGyms(
                defaultLiveSearch.placeQuery,
                defaultLiveSearch.query,
                initialRadiusMeters,
                controller.signal,
              )
            : Promise.reject(new Error("Invalid default live-search radius.")),
        ]);

        if (controller.signal.aborted) {
          return;
        }

        startTransition(() => {
          if (healthResult.status === "fulfilled") {
            setHealth(healthResult.value);
          }

          const publishedGyms =
            publishedResult.status === "fulfilled"
              ? publishedResult.value.results.map(buildPublishedBrowserGym)
              : [];
          setPublishedResults(publishedGyms);

          if (liveResult.status === "fulfilled") {
            applyLiveResponse(
              liveResult.value,
              defaultLiveSearch,
              {
                activateMode: true,
                syncControls: true,
                updateSelection: true,
                preferredSelectedGymId: publishedGyms[0]?.id ?? null,
              },
              {
                setMode,
                setLiveResults,
                setSelectedGymId,
                setLiveSearch,
                setLiveOrigin,
                setLiveSession,
              },
            );
            return;
          }

          setMode("published");
          setSelectedGymId(publishedGyms[0]?.id ?? null);
          setLiveSession(null);

          if (publishedGyms.length === 0) {
            setError(
              toUserFacingErrorMessage(
                liveResult.status === "rejected"
                  ? liveResult.reason
                  : new Error("No gyms were available."),
                "We couldn't load gyms right now.",
              ),
            );
            return;
          }

          if (liveResult.status === "rejected") {
            setError(
              toUserFacingErrorMessage(
                liveResult.reason,
                "Live search isn't available right now, so we're showing curated gyms instead.",
              ),
            );
          }
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

  useEffect(() => {
    if (!liveSession || liveSession.status !== "enriching") {
      return;
    }

    const controller = new AbortController();
    const pollDelayMs = Math.max(liveSession.pollAfterMs ?? 2000, 500);
    const timeoutId = window.setTimeout(() => {
      void getLiveSearchSession(liveSession.searchId, controller.signal)
        .then((response) => {
          if (controller.signal.aborted) {
            return;
          }
          applyLiveResponse(
            response,
            liveSearch,
            {
              activateMode: false,
              syncControls: false,
              updateSelection: mode === "live",
              preferredSelectedGymId: selectedGymId,
            },
            {
              setMode,
              setLiveResults,
              setSelectedGymId,
              setLiveSearch,
              setLiveOrigin,
              setLiveSession,
            },
          );
        })
        .catch((pollError: unknown) => {
          if (controller.signal.aborted) {
            return;
          }

          if (
            pollError instanceof DOMException
            && pollError.name === "AbortError"
          ) {
            return;
          }

          startTransition(() => {
            setLiveSession((current) =>
              current
                ? {
                    ...current,
                    status: "ready",
                    enrichmentStatus: "failed",
                    pollAfterMs: null,
                  }
                : current,
            );
          });
        });
    }, pollDelayMs);

    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [
    liveSearch,
    liveSession,
    mode,
    selectedGymId,
  ]);

  const visiblePublished = useMemo(
    () => filterGymsByQuery(publishedResults, deferredQuery),
    [publishedResults, deferredQuery],
  );

  const visibleLive = useMemo(
    () => filterGymsByQuery(liveResults, deferredQuery),
    [liveResults, deferredQuery],
  );

  const activeRows = mode === "published" ? visiblePublished : visibleLive;
  const hasLiveSearchRun = liveOrigin != null || liveResults.length > 0;

  const liveRadiusLabel = liveRadiusMiles != null
    ? formatMilesValue(liveRadiusMiles)
    : "n/a";
  const livePlaceLabel =
    liveSearch.resolvedLabel || liveOrigin?.label || liveSearch.placeQuery.trim() || "your chosen place";
  const liveSearchSummary =
    mode === "live"
      ? `${liveSearch.query.trim() || "gym"} within ${liveRadiusLabel} of ${livePlaceLabel}`
      : `Use Live Search to find gyms within a chosen radius of any place.`;
  const liveSearchIsRefreshing = liveSession?.status === "enriching";
  const liveSearchWasEnriched =
    liveSession?.enrichmentStatus === "completed" &&
    (liveSession?.revision ?? 0) > 0;
  const liveSearchEnrichmentFailed = liveSession?.enrichmentStatus === "failed";
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
        setLiveSession(null);
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
        "Enter a city, neighborhood, landmark, or ZIP code in the Place field to search around that place.",
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
      applyLiveResponse(
        response,
        nextLiveSearch,
        {
          activateMode: true,
          syncControls: true,
          updateSelection: true,
        },
        {
          setMode,
          setLiveResults,
          setSelectedGymId,
          setLiveSearch,
          setLiveOrigin,
          setLiveSession,
        },
      );
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
          liveRadiusLabel={liveRadiusLabel}
          livePlaceLabel={livePlaceLabel}
          hasLiveSearchRun={hasLiveSearchRun}
        />

        <StatusStrip
          health={health}
          mode={mode}
          liveSearchIsRefreshing={liveSearchIsRefreshing}
          liveSearchWasEnriched={liveSearchWasEnriched}
          liveSearchEnrichmentFailed={liveSearchEnrichmentFailed}
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
              hasLiveSearchRun={hasLiveSearchRun}
              liveSearchIsRefreshing={liveSearchIsRefreshing}
              liveSearchWasEnriched={liveSearchWasEnriched}
              liveSearchEnrichmentFailed={liveSearchEnrichmentFailed}
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
            <GeoCanvasPanel
              mode={mode}
              gyms={activeRows}
              selectedGymName={selectedGym?.name}
              selectedGymId={selectedGymId}
              onSelectGym={setSelectedGymId}
              nearbyLat={mode === "live" ? liveOrigin?.lat : undefined}
              nearbyLon={mode === "live" ? liveOrigin?.lon : undefined}
              livePlaceLabel={mode === "live" ? livePlaceLabel : undefined}
              liveRadiusLabel={mode === "live" ? liveRadiusLabel : undefined}
            />
            <SelectedGymPanel
              detailLoading={detailLoading}
              mode={mode}
              selectedGym={selectedGym}
              selectedActionLinks={selectedActionLinks}
            />
          </section>
        </div>
      </main>
    </div>
  );
}
