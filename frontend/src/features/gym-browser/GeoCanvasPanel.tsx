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
      title="Geo Canvas"
      subtitle={
        props.mode === "live"
          ? `Live pins for gyms within ${props.liveRadiusLabel ?? "your chosen radius"} of ${props.livePlaceLabel ?? "your selected place"}.`
          : "A spatial projection of the current published result set with selectable gym pins."
      }
      accent="Spatial Surface"
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
