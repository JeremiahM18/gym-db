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
  onModeChange: (mode: Mode) => void;
  onSelectGym: (gymId: string) => void;
};

export function ResultsPanel(props: ResultsPanelProps) {
  const activeRows =
    props.mode === "published" ? props.visiblePublished : props.visibleLive;

  return (
    <Panel
      title="Result Grid"
      subtitle="Switch between the curated published catalog and the live world search surface."
      accent="Browser Client"
    >
      <div className="results-context-banner">
        <strong>
          {props.mode === "published"
            ? "Published Catalog"
            : `Live Search within ${props.liveRadiusLabel} of ${props.livePlaceLabel}`}
        </strong>
        <span>
          {props.mode === "published"
            ? "These results come from the current GymDB published dataset."
            : props.liveSearchSummary}
        </span>
      </div>
      <div className="toolbar-row">
        <input
          className="search-input"
          value={props.query}
          onChange={(event) => props.onQueryChange(event.target.value)}
          placeholder={
            props.mode === "published"
              ? "Filter the published dataset by gym name, city, address, or specialty"
              : "Filter live results by gym name, city, or address"
          }
        />
        <div className="mode-chip-row">
          <button
            className={props.mode === "published" ? "chip active" : "chip"}
            type="button"
            onClick={() => props.onModeChange("published")}
          >
            Published Catalog
          </button>
          <button
            className={props.mode === "live" ? "chip active" : "chip"}
            type="button"
            onClick={() => props.onModeChange("live")}
            disabled={!props.visibleLive.length}
          >
            Live Search
          </button>
        </div>
      </div>

      <div className="result-list">
        {props.loading ? (
          <div className="empty-state">Loading live backend data...</div>
        ) : null}
        {!props.loading && !activeRows.length ? (
          <div className="empty-state">
            {props.mode === "published"
              ? "No published gyms matched these filters."
              : `No live gyms matched ${props.liveSearchSummary}. Try widening the radius or broadening the search.`}
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
                      <span className="mini-chip">Live result</span>
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
