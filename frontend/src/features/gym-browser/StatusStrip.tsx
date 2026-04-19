import type { HealthSnapshot } from "../../lib/api";

type StatusStripProps = {
  health: HealthSnapshot | null;
  apiBaseUrl: string;
};

export function StatusStrip(props: StatusStripProps) {
  return (
    <section className="status-strip status-strip-grid">
      <div className={`status-pill ${props.health?.live ? "healthy" : "degraded"}`}>
        <span className="status-dot" />
        API live: {props.health?.live ? "yes" : "unknown"}
      </div>
      <div className={`status-card ${props.health?.ready ? "healthy" : "degraded"}`}>
        <div className="status-card-head">
          <span className="status-dot" />
          <strong>Database readiness</strong>
        </div>
        <span>{props.health?.ready ? "all checks passing" : props.health?.readinessSummary ?? "check readiness"}</span>
        {props.health?.readinessHint ? (
          <small className="status-note">{props.health.readinessHint}</small>
        ) : null}
      </div>
      <div className="status-pill neutral">API base: {props.apiBaseUrl}</div>
    </section>
  );
}
