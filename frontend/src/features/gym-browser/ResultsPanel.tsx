import type { BrowserGym, Mode } from "./types";
import { Panel } from "../../components/Panel";
import { formatConfidence, formatMilesFromMeters, titleCase } from "./utils";

type ResultsPanelProps = {
  query: string;
  mode: Mode;
  loading: boolean;
  hasLiveSearchRun: boolean;
  selectedGymId: string | null;
  visiblePublished: BrowserGym[];
  visibleLive: BrowserGym[];
  livePlaceLabel: string;
  liveRadiusLabel: string;
  liveSearchSummary: string;
  onQueryChange: (value: string) => void;
  onExpandLiveRadius: () => void;
  onSwitchToLiveMode: () => void;
  onSelectGym: (gymId: string) => void;
};

export function ResultsPanel(props: ResultsPanelProps) {
  const activeRows =
    props.mode === "published" ? props.visiblePublished : props.visibleLive;
  const loadingPlaceholders = Array.from({ length: 4 }, (_, index) => index);

  return (
    <Panel
      title="Gyms"
      subtitle={
        props.mode === "published"
          ? "Review the tighter shortlist."
          : props.hasLiveSearchRun
            ? `See gyms within ${props.liveRadiusLabel} of the place you chose: ${props.livePlaceLabel}.`
            : "Gyms around the place you choose will appear here."
      }
      accent="Results"
    >
      <div className="results-context-banner">
        <strong>
          {props.mode === "published"
            ? `${activeRows.length} curated picks`
            : props.hasLiveSearchRun
              ? `${activeRows.length} gyms within ${props.liveRadiusLabel} of ${props.livePlaceLabel}`
              : "Start with a place and radius"}
        </strong>
        <span>
          {props.mode === "published"
            ? "Use this tighter view when you want a cleaner shortlist to compare."
            : props.hasLiveSearchRun
              ? props.liveSearchSummary
              : "Enter a city, neighborhood, landmark, or ZIP code to search around that place."}
        </span>
      </div>
      <div className="toolbar-row toolbar-row-single">
        <input
          className="search-input"
          value={props.query}
          onChange={(event) => props.onQueryChange(event.target.value)}
          placeholder={
            props.mode === "published"
              ? "Filter curated gyms by name, area, address, or style"
              : "Filter live results by gym name, area, or address"
          }
        />
      </div>

      <div className="result-list">
        {props.loading ? (
          loadingPlaceholders.map((placeholder) => (
            <div key={placeholder} className="result-card skeleton-card" aria-hidden="true">
              <div className="result-primary">
                <div className="skeleton skeleton-line skeleton-line-title" />
                <div className="skeleton skeleton-line" />
                <div className="skeleton skeleton-line skeleton-line-short" />
              </div>
              <div className="result-metrics">
                <div className="skeleton skeleton-pill" />
                <div className="skeleton skeleton-pill skeleton-pill-short" />
              </div>
            </div>
          ))
        ) : null}
        {!props.loading && !activeRows.length ? (
          <div className="empty-state">
            <div className="empty-state-content">
              <strong>
                {props.mode === "published"
                  ? "No curated gyms matched these filters."
                  : props.hasLiveSearchRun
                    ? "No gyms matched this search yet."
                    : "Search for a place to start exploring."}
              </strong>
              <p>
                {props.mode === "published"
                  ? "Try broadening the filters or switch back to place search to explore a wider area."
                  : props.hasLiveSearchRun
                    ? `We didn’t find gyms for ${props.liveSearchSummary}. Widen the radius or search a nearby place.`
                    : "Choose a place, pick a radius, and we’ll show gyms around that place here."}
              </p>
              <div className="empty-state-actions">
                {props.mode === "published" ? (
                  <button
                    type="button"
                    className="chip active"
                    onClick={props.onSwitchToLiveMode}
                  >
                    Go back to place search
                  </button>
                ) : (
                  <button
                    type="button"
                    className="chip active"
                    onClick={props.onExpandLiveRadius}
                  >
                    {props.hasLiveSearchRun ? "Widen the radius" : "Try a wider radius"}
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : null}
        {!props.loading
          ? activeRows.map((gym) => (
              <button
                key={gym.id}
                type="button"
                className={
                  props.selectedGymId === gym.id ? "result-card active" : "result-card"
                }
                onClick={() => props.onSelectGym(gym.id)}
              >
                <div className="result-primary">
                  <div className="result-topline">
                    <strong>{gym.name}</strong>
                    <span className="city-pill">{gym.cityState}</span>
                  </div>
                  <p className="result-subcopy">
                    {gym.address ?? "Coordinates available"}
                  </p>
                  <div className="result-chip-row">
                    {gym.specialty ? (
                      <span className="mini-chip">{titleCase(gym.specialty)}</span>
                    ) : null}
                    {gym.website ? <span className="mini-chip">Website</span> : null}
                    {gym.phone ? <span className="mini-chip">Phone</span> : null}
                    {gym.is247 ? <span className="mini-chip">Open 24/7</span> : null}
                    {gym.openingHours && !gym.is247 ? (
                      <span className="mini-chip">Hours listed</span>
                    ) : null}
                    {gym.sourceKind === "live" ? (
                      <span className="mini-chip">Nearby</span>
                    ) : null}
                  </div>
                </div>
                <div className="result-metrics">
                  <span>
                    {gym.distanceM != null
                      ? formatMilesFromMeters(gym.distanceM)
                      : gym.confidenceScore != null
                        ? formatConfidence(gym.confidenceScore)
                        : "live"}
                  </span>
                  <span>{gym.tier ? titleCase(gym.tier) : "Gym"}</span>
                </div>
              </button>
            ))
          : null}
      </div>
    </Panel>
  );
}
