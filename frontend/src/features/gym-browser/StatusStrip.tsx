import type { Mode } from "./types";
import type { HealthSnapshot } from "../../lib/api";

type StatusStripProps = {
  health: HealthSnapshot | null;
  mode: Mode;
  liveSearchIsRefreshing: boolean;
  liveSearchWasEnriched: boolean;
  liveSearchEnrichmentFailed: boolean;
};

export function StatusStrip(props: StatusStripProps) {
  let liveSearchMessage =
    "Use place search for nearby results. Use curated picks for the published catalog.";

  if (props.mode === "live" && props.liveSearchIsRefreshing) {
    liveSearchMessage =
      "Refreshing these results with OpenStreetMap details.";
  } else if (props.mode === "live" && props.liveSearchWasEnriched) {
    liveSearchMessage = "OpenStreetMap details were added to these results.";
  } else if (props.mode === "live" && props.liveSearchEnrichmentFailed) {
    liveSearchMessage =
      "Showing the TomTom snapshot because OSM enrichment was unavailable.";
  }

  return (
    <section className="status-strip status-strip-grid">
      <div className={`status-pill ${props.health?.live ? "healthy" : "degraded"}`}>
        <span className="status-dot" />
        Search service: {props.health?.live ? "ready" : "unavailable"}
      </div>
      <div className={`status-card ${props.health?.ready ? "healthy" : "degraded"}`}>
        <div className="status-card-head">
          <span className="status-dot" />
          <strong>Data readiness</strong>
        </div>
        <span>{props.health?.ready ? "ready" : props.health?.readinessSummary ?? "checking"}</span>
        {props.health?.readinessHint ? (
          <small className="status-note">{props.health.readinessHint}</small>
        ) : null}
      </div>
      <div className="status-pill neutral">{liveSearchMessage}</div>
    </section>
  );
}
