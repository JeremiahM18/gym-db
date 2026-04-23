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
    "Place search uses the Place field and radius below. Curated picks is there when you want a tighter shortlist.";

  if (props.mode === "live" && props.liveSearchIsRefreshing) {
    liveSearchMessage =
      "Refreshing this same search with OpenStreetMap details while keeping the current results on screen.";
  } else if (props.mode === "live" && props.liveSearchWasEnriched) {
    liveSearchMessage =
      "OpenStreetMap details have been applied to this live search.";
  } else if (props.mode === "live" && props.liveSearchEnrichmentFailed) {
    liveSearchMessage =
      "Showing the initial TomTom results while extra public details were unavailable.";
  }

  return (
    <section className="status-strip status-strip-grid">
      <div className={`status-pill ${props.health?.live ? "healthy" : "degraded"}`}>
        <span className="status-dot" />
        Search service: {props.health?.live ? "ready" : "warming up"}
      </div>
      <div className={`status-card ${props.health?.ready ? "healthy" : "degraded"}`}>
        <div className="status-card-head">
          <span className="status-dot" />
          <strong>Data readiness</strong>
        </div>
        <span>{props.health?.ready ? "all checks passing" : props.health?.readinessSummary ?? "checking status"}</span>
        {props.health?.readinessHint ? (
          <small className="status-note">{props.health.readinessHint}</small>
        ) : null}
      </div>
      <div className="status-pill neutral">{liveSearchMessage}</div>
    </section>
  );
}
