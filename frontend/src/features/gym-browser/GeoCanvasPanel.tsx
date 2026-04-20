import { GeoMap } from "../../components/GeoMap";
import { Panel } from "../../components/Panel";
import type { BrowserGym, Mode } from "./types";

type GeoCanvasPanelProps = {
  mode: Mode;
  gyms: BrowserGym[];
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
          ? `Pins for gyms within ${props.liveRadiusLabel ?? "your chosen radius"} of ${props.livePlaceLabel ?? "your selected place"}.`
          : "A map view of the curated gyms in the current result list."
      }
      accent="Search Area"
    >
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
