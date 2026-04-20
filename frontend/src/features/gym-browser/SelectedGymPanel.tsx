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
      ? "A closer look at the selected gym from your tighter shortlist."
      : "Contact details, amenities, and distance for the gym you selected.";

  if (props.detailLoading) {
    return (
      <Panel title="Gym Details" subtitle={subtitle} accent="Selected Gym">
        <div className="empty-state">Loading the selected gym...</div>
      </Panel>
    );
  }

  if (!props.selectedGym) {
    return (
      <Panel title="Gym Details" subtitle={subtitle} accent="Selected Gym">
        <div className="empty-state">
          Pick a gym from the list to see hours, amenities, contact details, and overall fit.
        </div>
      </Panel>
    );
  }

  return (
    <Panel title="Gym Details" subtitle={subtitle} accent="Selected Gym">
      <div className="detail-grid">
        <div className="detail-headline">
          <div>
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

        <div className="detail-spotlight">
          <div>
            <span className="detail-spotlight-label">At a glance</span>
            <strong>
              {props.selectedGym.distanceM != null
                ? `${formatMilesFromMeters(props.selectedGym.distanceM)} away`
                : "Ready to compare"}
            </strong>
            <p>
              {props.selectedGym.address ??
                "Address details are still limited, but this gym is included in the current search."}
            </p>
          </div>
          <div className="detail-spotlight-meta">
            {props.selectedGym.is247 ? <span className="mini-chip">Open 24/7</span> : null}
            {props.selectedGym.website ? <span className="mini-chip">Has website</span> : null}
            {props.selectedGym.phone ? <span className="mini-chip">Has phone</span> : null}
            {props.selectedGym.lifterFriendly ? (
              <span className="mini-chip">Lifter-friendly</span>
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
            label="View"
            value={props.selectedGym.sourceKind === "published" ? "Curated picks" : "Nearby search"}
            tone="cool"
          />
          <StatCard
            label="Area"
            value={props.selectedGym.cityState}
            tone="warm"
          />
          <StatCard
            label="Distance"
            value={
              props.selectedGym.distanceM != null
                ? formatMilesFromMeters(props.selectedGym.distanceM)
                : "n/a"
            }
          />
          <StatCard
            label="Match quality"
            value={
              props.selectedGym.confidenceScore != null
                ? formatConfidence(props.selectedGym.confidenceScore)
                : props.selectedGym.is247
                  ? "24/7"
                  : "Available"
            }
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
                <p className="detail-copy">No extra amenities were listed for this gym yet.</p>
              )}
            </div>
            <p className="detail-copy">
              {props.selectedGym.sourceKind === "published"
                ? "Curated picks give you a cleaner shortlist when you want to compare fit, quality, and amenities."
                : "Nearby results help you compare gyms around a real place, with stronger public details filled in when available."}
            </p>
          </section>
        </div>
      </div>
    </Panel>
  );
}
