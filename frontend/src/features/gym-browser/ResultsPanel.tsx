import type { GymOutV2 } from "../../lib/api";
import { Panel } from "../../components/Panel";
import type { Mode } from "./types";
import {
  formatConfidence,
  formatMilesFromMeters,
  getAddress,
  getCityState,
  getPhone,
  getWebsite,
  haversineMeters,
  inferBoolean,
  inferString,
  titleCase,
} from "./utils";

type ResultsPanelProps = {
  query: string;
  mode: Mode;
  loading: boolean;
  selectedGymId: string | null;
  visibleCatalog: GymOutV2[];
  visibleNearby: GymOutV2[];
  nearbyLat?: number;
  nearbyLon?: number;
  onQueryChange: (value: string) => void;
  onModeChange: (mode: Mode) => void;
  onSelectGym: (gymId: string) => void;
};

export function ResultsPanel(props: ResultsPanelProps) {
  const activeRows = props.mode === "catalog" ? props.visibleCatalog : props.visibleNearby;

  return (
    <Panel
      title="Result Grid"
      subtitle="Deferred local search keeps browsing responsive while live filters stay server-backed."
      accent="Browser Client"
    >
      <div className="toolbar-row">
        <input
          className="search-input"
          value={props.query}
          onChange={(event) => props.onQueryChange(event.target.value)}
          placeholder="Search loaded results by name, city, street, or specialty"
        />
        <div className="mode-chip-row">
          <button
            className={props.mode === "catalog" ? "chip active" : "chip"}
            type="button"
            onClick={() => props.onModeChange("catalog")}
          >
            Catalog
          </button>
          <button
            className={props.mode === "nearby" ? "chip active" : "chip"}
            type="button"
            onClick={() => props.onModeChange("nearby")}
            disabled={!props.visibleNearby.length}
          >
            Nearby
          </button>
        </div>
      </div>

      <div className="result-list">
        {props.loading ? <div className="empty-state">Loading live backend data...</div> : null}
        {!props.loading && !activeRows.length ? (
          <div className="empty-state">No gyms matched this query.</div>
        ) : null}
        {!props.loading && props.mode === "catalog"
          ? props.visibleCatalog.map((gym) => {
              const website = getWebsite(gym);
              const phone = getPhone(gym);

              return (
                <button
                  key={gym.id}
                  type="button"
                  className={props.selectedGymId === gym.id ? "result-card active" : "result-card"}
                  onClick={() => props.onSelectGym(gym.id)}
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
                      {inferBoolean(gym, "is_24_7") === "Yes" ? (
                        <span className="mini-chip">24/7</span>
                      ) : null}
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
        {!props.loading && props.mode === "nearby"
          ? props.visibleNearby.map((gym) => {
              const miles =
                props.nearbyLat != null && props.nearbyLon != null
                  ? formatMilesFromMeters(
                      haversineMeters(props.nearbyLat, props.nearbyLon, gym.lat, gym.lon),
                    )
                  : null;

              return (
                <button
                  key={gym.id}
                  type="button"
                  className={props.selectedGymId === gym.id ? "result-card active" : "result-card"}
                  onClick={() => props.onSelectGym(gym.id)}
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
  );
}
