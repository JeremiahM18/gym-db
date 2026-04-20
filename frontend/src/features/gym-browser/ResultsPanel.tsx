import type { BrowserGym, Mode } from "./types";
import { Panel } from "../../components/Panel";
import { formatConfidence, formatMilesFromMeters, titleCase } from "./utils";

type ResultsPanelProps = {
  query: string;
  mode: Mode;
  loading: boolean;
  selectedGymId: string | null;
  visiblePublished: BrowserGym[];
  visibleLive: BrowserGym[];
  livePlaceLabel: string;
  liveRadiusLabel: string;
  liveSearchSummary: string;
  onQueryChange: (value: string) => void;
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
          ? "Browse the current curated GymDB results."
          : `See gyms within ${props.liveRadiusLabel} of ${props.livePlaceLabel}.`
      }
      accent="Results"
    >
      <div className="results-context-banner">
        <strong>
          {props.mode === "published"
            ? `${activeRows.length} curated gyms`
            : `${activeRows.length} gyms within ${props.liveRadiusLabel} of ${props.livePlaceLabel}`}
        </strong>
        <span>
          {props.mode === "published"
            ? "This list uses the current curated GymDB catalog."
            : props.liveSearchSummary}
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
            {props.mode === "published"
              ? "No curated gyms matched these filters. Try broadening the filters or switching back to place search."
              : `No gyms matched ${props.liveSearchSummary}. Try widening the radius or searching a nearby place.`}
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
                  <span>
                    {gym.specialty ? titleCase(gym.specialty) : gym.sourceLabel}
                  </span>
                  <p className="result-subcopy">
                    {gym.address ?? "Coordinates available"}
                  </p>
                  <div className="result-chip-row">
                    {gym.website ? <span className="mini-chip">Website</span> : null}
                    {gym.phone ? <span className="mini-chip">Phone</span> : null}
                    {gym.is247 ? <span className="mini-chip">24/7</span> : null}
                    {gym.sourceKind === "live" ? (
                      <span className="mini-chip">Nearby match</span>
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
                  <span>{gym.tier ? titleCase(gym.tier) : gym.sourceLabel}</span>
                </div>
              </button>
            ))
          : null}
      </div>
    </Panel>
  );
}
