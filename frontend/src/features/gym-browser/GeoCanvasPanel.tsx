import { GeoMap } from "../../components/GeoMap";
import { Panel } from "../../components/Panel";
import type { BrowserGym, Mode } from "./types";

type GeoCanvasPanelProps = {
  mode: Mode;
  gyms: BrowserGym[];
  selectedGymName?: string;
  selectedGymId: string | null;
  onSelectGym: (gymId: string) => void;
  nearbyLat?: number;
  nearbyLon?: number;
  livePlaceLabel?: string;
  liveRadiusLabel?: string;
};

export function GeoCanvasPanel(props: GeoCanvasPanelProps) {
  return (
    <Panel
      title="Map"
      subtitle={
        props.mode === "live"
          ? `See the search center, nearby gyms, and the selected result in one spatial view.`
          : "Use the map to compare where your shortlisted gyms cluster."
      }
      accent="Map View"
    >
      <div className="map-summary-row">
        <div className="map-summary-card">
          <span>Search area</span>
          <strong>
            {props.mode === "live"
              ? `${props.liveRadiusLabel ?? "Your radius"} around ${props.livePlaceLabel ?? "your selected place"}`
              : `${props.gyms.length} curated picks on the map`}
          </strong>
        </div>
        <div className="map-summary-card">
          <span>Current focus</span>
          <strong>{props.selectedGymName ?? "Select a gym from the list"}</strong>
        </div>
      </div>
      <GeoMap
        gyms={props.gyms}
        selectedGymId={props.selectedGymId}
        onSelect={props.onSelectGym}
        nearbyLat={props.nearbyLat}
        nearbyLon={props.nearbyLon}
      />
    </Panel>
  );
}
