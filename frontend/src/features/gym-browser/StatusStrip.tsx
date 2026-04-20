import type { HealthSnapshot } from "../../lib/api";

type StatusStripProps = {
  health: HealthSnapshot | null;
};

export function StatusStrip(props: StatusStripProps) {
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
      <div className="status-pill neutral">Nearby search is the main path. Curated picks is there when you want a tighter shortlist.</div>
    </section>
  );
}
