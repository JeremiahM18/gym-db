import { ActionPill } from "../../components/ActionPill";
import { StatCard } from "../../components/StatCard";
import type { ActionLink, Mode } from "./types";

type HeroSectionProps = {
  mode: Mode;
  activeRowCount: number;
  averageConfidence: string;
  nearbyRadiusLabel: string;
  topSpecialty: string;
  selectedActionLinks: ActionLink[];
};

export function HeroSection(props: HeroSectionProps) {
  return (
    <section className="hero">
      <div>
        <p className="eyebrow">GymDB Browser Client</p>
        <h1>Find gyms, inspect inference, and jump straight into places you can actually visit.</h1>
        <p className="hero-copy">
          Browse the live catalog, filter by specialty and quality, run nearby search without a
          database-only dependency, and jump out to maps or official gym sites in one flow.
        </p>
        <div className="hero-actions">
          {props.selectedActionLinks.slice(0, 3).map((link) => (
            <ActionPill key={link.href} {...link} />
          ))}
        </div>
      </div>
      <div className="hero-grid">
        <StatCard label="Mode" value={props.mode === "catalog" ? "Catalog" : "Nearby"} tone="warm" />
        <StatCard label="Visible gyms" value={String(props.activeRowCount)} tone="cool" />
        <StatCard label="Avg confidence" value={props.averageConfidence} />
        <StatCard
          label="Search radius"
          value={props.mode === "nearby" ? props.nearbyRadiusLabel : "Catalog"}
        />
        <StatCard label="Lead specialty" value={props.topSpecialty} />
      </div>
    </section>
  );
}
