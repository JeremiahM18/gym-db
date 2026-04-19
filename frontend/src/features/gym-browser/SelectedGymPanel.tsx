import { ActionPill } from "../../components/ActionPill";
import { Panel } from "../../components/Panel";
import { StatCard } from "../../components/StatCard";
import type { ActionLink, BrowserGym, Mode } from "./types";
import { formatConfidence, formatMilesFromMeters, titleCase } from "./utils";

type SelectedGymPanelProps = {
  detailLoading: boolean;
  mode: Mode;
  selectedGym: BrowserGym | null;
  selectedActionLinks: ActionLink[];
};

export function SelectedGymPanel(props: SelectedGymPanelProps) {
  const subtitle =
    props.mode === "published"
      ? "Curated catalog detail with explainable inference, operator facts, and public contact surface."
      : "Live search detail for the selected gym result, with fast outbound actions and place context.";

  if (props.detailLoading) {
    return (
      <Panel title="Selected Gym" subtitle={subtitle} accent="Explainability">
        <div className="empty-state">Loading selected gym...</div>
      </Panel>
    );
  }

  if (!props.selectedGym) {
    return (
      <Panel title="Selected Gym" subtitle={subtitle} accent="Explainability">
        <div className="empty-state">Select a gym to inspect the current result.</div>
      </Panel>
    );
  }

  return (
    <Panel title="Selected Gym" subtitle={subtitle} accent="Explainability">
      <div className="detail-grid">
        <div className="detail-headline">
          <div>
            <p className="eyebrow">{props.selectedGym.id}</p>
            <h3>{props.selectedGym.name}</h3>
            <p className="detail-summary">
              {props.selectedGym.cityState}
              {props.selectedGym.specialty
                ? ` · ${titleCase(props.selectedGym.specialty)}`
                : ""}
              {props.selectedGym.tier ? ` · ${titleCase(props.selectedGym.tier)}` : ""}
            </p>
          </div>
          <div className="detail-badges">
            <span>{props.selectedGym.sourceLabel}</span>
            {props.selectedGym.specialty ? (
              <span>{titleCase(props.selectedGym.specialty)}</span>
            ) : null}
            {props.selectedGym.confidenceScore != null ? (
              <span>{formatConfidence(props.selectedGym.confidenceScore)}</span>
            ) : null}
            {props.selectedGym.distanceM != null ? (
              <span>{formatMilesFromMeters(props.selectedGym.distanceM)}</span>
            ) : null}
          </div>
        </div>

        <div className="action-rail">
          {props.selectedActionLinks.map((link) => (
            <ActionPill key={link.href} {...link} />
          ))}
        </div>

        <div className="detail-facts">
          <StatCard
            label="Source"
            value={props.selectedGym.sourceLabel}
            tone="cool"
          />
          <StatCard
            label="City"
            value={props.selectedGym.cityState}
            tone="warm"
          />
          <StatCard
            label="Search distance"
            value={
              props.selectedGym.distanceM != null
                ? formatMilesFromMeters(props.selectedGym.distanceM)
                : "n/a"
            }
          />
          <StatCard
            label="Inference engine"
            value={props.selectedGym.inferenceEngine ?? "n/a"}
          />
        </div>

        <div className="detail-columns">
          <section className="detail-section">
            <h4>Visit and Contact</h4>
            <div className="fact-list">
              <div className="fact-row">
                <span>Address</span>
                <strong>
                  {props.selectedGym.address ?? "No structured address was published"}
                </strong>
              </div>
              <div className="fact-row">
                <span>Hours</span>
                <strong>
                  {props.selectedGym.openingHours ?? "Hours not published"}
                </strong>
              </div>
              <div className="fact-row">
                <span>Phone</span>
                <strong>{props.selectedGym.phone ?? "No phone published"}</strong>
              </div>
              <div className="fact-row">
                <span>Email</span>
                <strong>{props.selectedGym.email ?? "No email published"}</strong>
              </div>
            </div>
          </section>

          <section className="detail-section">
            <h4>Signals and Amenities</h4>
            <div className="tag-cloud">
              {props.selectedGym.amenityChips.length ? (
                props.selectedGym.amenityChips.map((chip) => (
                  <span key={chip} className="tag-pill">
                    {chip}
                  </span>
                ))
              ) : (
                <p className="detail-copy">No extra amenity signals were published.</p>
              )}
            </div>
            <p className="detail-copy">
              {props.selectedGym.sourceKind === "published"
                ? "Published catalog entries include GymDB inference and curation metadata."
                : "Live search entries are direct TomTom POI results and do not include GymDB inference yet."}
            </p>
          </section>
        </div>
      </div>
    </Panel>
  );
}
