import type { HealthSnapshot } from "../../lib/api";

type StatusStripProps = {
  health: HealthSnapshot | null;
  apiBaseUrl: string;
};

export function StatusStrip(props: StatusStripProps) {
  return (
    <section className="status-strip">
      <div className={`status-pill ${props.health?.live ? "healthy" : "degraded"}`}>
        <span className="status-dot" />
        API live: {props.health?.live ? "yes" : "unknown"}
      </div>
      <div className={`status-pill ${props.health?.ready ? "healthy" : "degraded"}`}>
        <span className="status-dot" />
        Backend ready: {props.health?.ready ? "yes" : "check readiness"}
      </div>
      <div className="status-pill neutral">API base: {props.apiBaseUrl}</div>
    </section>
  );
}
