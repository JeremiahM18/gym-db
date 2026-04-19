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
        <p className="eyebrow">GymDB Full-Stack Search</p>
        <h1>Search the live world for gyms, then drop into the curated catalog when you want verified operator data.</h1>
        <p className="hero-copy">
          Live Search is powered by TomTom place search. Published Catalog stays in the product as
          the curated GymDB dataset with inference, quality filters, and explainable operator
          detail.
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
          value={props.mode === "live" ? props.nearbyRadiusLabel : "Published"}
        />
        <StatCard
          label={props.mode === "published" ? "Lead specialty" : "Lead area"}
          value={props.topSpecialty}
        />
      </div>
    </section>
  );
}
