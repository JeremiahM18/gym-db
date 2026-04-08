import { ActionPill } from "../../components/ActionPill";
import { Panel } from "../../components/Panel";
import { StatCard } from "../../components/StatCard";
import type { GymOutV2 } from "../../lib/api";
import type { ActionLink } from "./types";
import {
  formatConfidence,
  getAddress,
  getAmenityChips,
  getCityState,
  getEmail,
  getOpeningHours,
  getPhone,
  inferBoolean,
  inferString,
  titleCase,
} from "./utils";

type SelectedGymPanelProps = {
  detailLoading: boolean;
  selectedGym: GymOutV2 | null;
  selectedActionLinks: ActionLink[];
};

export function SelectedGymPanel(props: SelectedGymPanelProps) {
  if (props.detailLoading) {
    return (
      <Panel
        title="Selected Gym"
        subtitle="Action links, operator facts, public contact surface, and explainable inference from the live v2 contract."
        accent="Explainability"
      >
        <div className="empty-state">Loading selected gym...</div>
      </Panel>
    );
  }

  if (!props.selectedGym) {
    return (
      <Panel
        title="Selected Gym"
        subtitle="Action links, operator facts, public contact surface, and explainable inference from the live v2 contract."
        accent="Explainability"
      >
        <div className="empty-state">Select a gym to inspect the full public surface.</div>
      </Panel>
    );
  }

  const selectedCity = getCityState(props.selectedGym);
  const visibleSelectedSpecialty = titleCase(
    inferString(props.selectedGym, "specialty", "general_fitness"),
  );
  const visibleSelectedAddress = getAddress(props.selectedGym);
  const visibleSelectedHours = getOpeningHours(props.selectedGym);
  const visibleSelectedAmenities = getAmenityChips(props.selectedGym);

  return (
    <Panel
      title="Selected Gym"
      subtitle="Action links, operator facts, public contact surface, and explainable inference from the live v2 contract."
      accent="Explainability"
    >
      <div className="detail-grid">
        <div className="detail-headline">
          <div>
            <p className="eyebrow">{props.selectedGym.id}</p>
            <h3>{props.selectedGym.name}</h3>
            <p className="detail-summary">
              {selectedCity} · {props.selectedGym.inference_summary?.specialty ?? visibleSelectedSpecialty} ·{" "}
              {props.selectedGym.inference_summary?.tier ??
                inferString(props.selectedGym, "tier", "Unknown")}
            </p>
          </div>
          <div className="detail-badges">
            <span>{visibleSelectedSpecialty}</span>
            <span>{titleCase(inferString(props.selectedGym, "tier", "unknown"))}</span>
            <span>{formatConfidence(props.selectedGym.confidence_score)}</span>
          </div>
        </div>

        <div className="action-rail">
          {props.selectedActionLinks.map((link) => (
            <ActionPill key={link.href} {...link} />
          ))}
        </div>

        <div className="detail-facts">
          <StatCard
            label="Lifter friendly"
            value={inferBoolean(props.selectedGym, "lifter_friendly")}
            tone="cool"
          />
          <StatCard
            label="24/7 access"
            value={inferBoolean(props.selectedGym, "is_24_7")}
            tone="warm"
          />
          <StatCard label="City" value={selectedCity} />
          <StatCard label="Inference engine" value={props.selectedGym.inference_meta.engine} />
        </div>

        <div className="detail-columns">
          <section className="detail-section">
            <h4>Visit and Contact</h4>
            <div className="fact-list">
              <div className="fact-row">
                <span>Address</span>
                <strong>{visibleSelectedAddress ?? "No structured address in source tags"}</strong>
              </div>
              <div className="fact-row">
                <span>Hours</span>
                <strong>{visibleSelectedHours ?? "Hours not published"}</strong>
              </div>
              <div className="fact-row">
                <span>Phone</span>
                <strong>{getPhone(props.selectedGym) ?? "No phone in source tags"}</strong>
              </div>
              <div className="fact-row">
                <span>Email</span>
                <strong>{getEmail(props.selectedGym) ?? "No email in source tags"}</strong>
              </div>
            </div>
          </section>

          <section className="detail-section">
            <h4>Signals and Amenities</h4>
            <div className="tag-cloud">
              {visibleSelectedAmenities.length ? (
                visibleSelectedAmenities.map((chip) => (
                  <span key={chip} className="tag-pill">
                    {chip}
                  </span>
                ))
              ) : (
                <p className="detail-copy">No prominent amenity tags were published for this gym.</p>
              )}
            </div>
            <p className="detail-copy">
              OSM refs: {props.selectedGym.osm_refs.length} linked source record
              {props.selectedGym.osm_refs.length === 1 ? "" : "s"}.
            </p>
          </section>
        </div>

        <div className="inference-table">
          {Object.entries(props.selectedGym.inference).map(([key, value]) => (
            <article key={key} className="inference-row">
              <div>
                <p className="inference-key">{titleCase(key)}</p>
                <strong>{String(value.value)}</strong>
              </div>
              <div>
                <p className="inference-meta">
                  Confidence {formatConfidence(value.confidence ?? null)}
                </p>
                <p className="inference-reasons">{value.reasons.join(" • ") || "No explicit reasons"}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </Panel>
  );
}
