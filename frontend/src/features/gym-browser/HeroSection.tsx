import { ActionPill } from "../../components/ActionPill";
import { StatCard } from "../../components/StatCard";
import type { ActionLink, Mode } from "./types";

type HeroSectionProps = {
  mode: Mode;
  activeRowCount: number;
  averageConfidence: string;
  liveRadiusLabel: string;
  livePlaceLabel: string;
  liveSearchSummary: string;
  topSpecialty: string;
  selectedActionLinks: ActionLink[];
};

export function HeroSection(props: HeroSectionProps) {
  return (
    <section className="hero">
      <div>
        <p className="eyebrow">Find the Right Gym</p>
        <h1>Search for gyms around any place, then compare the best matches without losing the map.</h1>
        <p className="hero-copy">
          Start with a city, neighborhood, landmark, or ZIP code. Choose a radius, browse nearby
          gyms, and compare hours, amenities, and contact details in one workspace.
        </p>
        <p className="hero-live-summary">
          {props.mode === "live"
            ? `Searching now: ${props.liveSearchSummary}.`
            : "Use curated gyms when you want the tighter GymDB view of the current catalog."}
        </p>
        <div className="hero-value-row">
          <div className="hero-value-card">
            <span>Best for</span>
            <strong>
              {props.mode === "live" ? "Exploring a real area" : "Reviewing quality picks"}
            </strong>
          </div>
          <div className="hero-value-card">
            <span>What stands out</span>
            <strong>
              {props.mode === "live"
                ? "Distance-first discovery"
                : "Stronger signals and fit"}
            </strong>
          </div>
        </div>
        <div className="hero-actions">
          {props.selectedActionLinks.slice(0, 3).map((link) => (
            <ActionPill key={link.href} {...link} />
          ))}
        </div>
      </div>
      <div className="hero-grid">
        <StatCard
          label="View"
          value={props.mode === "published" ? "Curated gyms" : "Live nearby search"}
          tone="warm"
        />
        <StatCard label="Gyms showing" value={String(props.activeRowCount)} tone="cool" />
        <StatCard
          label={props.mode === "published" ? "Average quality" : "Best match"}
          value={props.mode === "published" ? props.averageConfidence : props.topSpecialty}
        />
        <StatCard
          label="Radius"
          value={props.mode === "live" ? props.liveRadiusLabel : "Curated"}
        />
        <StatCard
          label={props.mode === "published" ? "Top gym style" : "Search area"}
          value={props.mode === "published" ? props.topSpecialty : props.livePlaceLabel}
        />
      </div>
    </section>
  );
}
