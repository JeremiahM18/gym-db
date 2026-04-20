import type { Mode } from "./types";

type HeroSectionProps = {
  mode: Mode;
  activeRowCount: number;
  liveRadiusLabel: string;
  livePlaceLabel: string;
  hasLiveSearchRun: boolean;
};

export function HeroSection(props: HeroSectionProps) {
  return (
    <section className="hero">
      <div className="hero-brand">
        <p className="eyebrow">GymDB</p>
        <h1>Find gyms near any place.</h1>
        <p className="hero-copy">
          Search by place, set a radius, and compare nearby gyms with the map and details in
          view.
        </p>
      </div>
      <div className="hero-utility">
        <div className="hero-mode-pill">
          {props.mode === "published" ? "Curated picks" : "Nearby search"}
        </div>
        <div className="hero-context-grid">
          <div className="hero-context-card">
            <span>Search area</span>
            <strong>
              {props.mode === "published"
                ? "Current GymDB catalog"
                : props.hasLiveSearchRun
                  ? props.livePlaceLabel
                  : "Choose a place"}
            </strong>
          </div>
          <div className="hero-context-card">
            <span>Showing</span>
            <strong>{props.activeRowCount} gyms</strong>
          </div>
          <div className="hero-context-card">
            <span>Radius</span>
            <strong>{props.mode === "published" ? "Shortlist" : props.liveRadiusLabel}</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
