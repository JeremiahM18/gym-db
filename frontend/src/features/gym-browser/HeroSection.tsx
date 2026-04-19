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
        <p className="eyebrow">GymDB Full-Stack Search</p>
        <h1>Search for gyms within a real-world radius, then compare them against the curated catalog when you want verified operator detail.</h1>
        <p className="hero-copy">
          Live Search is now OpenStreetMap-first: pick a place, choose a radius, and see gyms by
          distance with GymDB inference on top. TomTom resolves the place and then verifies or
          enriches matching gyms when it can.
        </p>
        <p className="hero-live-summary">
          {props.mode === "live"
            ? `Live now: ${props.liveSearchSummary}.`
            : "Use Live Search when you want the real world. Use Published Catalog when you want the curated GymDB snapshot."}
        </p>
        <div className="hero-actions">
          {props.selectedActionLinks.slice(0, 3).map((link) => (
            <ActionPill key={link.href} {...link} />
          ))}
        </div>
      </div>
      <div className="hero-grid">
        <StatCard
          label="Mode"
          value={props.mode === "published" ? "Published Catalog" : "Live Search"}
          tone="warm"
        />
        <StatCard label="Visible gyms" value={String(props.activeRowCount)} tone="cool" />
        <StatCard
          label={props.mode === "published" ? "Avg confidence" : "Source"}
          value={props.mode === "published" ? props.averageConfidence : "TomTom"}
        />
        <StatCard
          label="Search radius"
          value={props.mode === "live" ? props.liveRadiusLabel : "Published"}
        />
        <StatCard
          label={props.mode === "published" ? "Lead specialty" : "Search origin"}
          value={props.mode === "published" ? props.topSpecialty : props.livePlaceLabel}
        />
      </div>
    </section>
  );
}
