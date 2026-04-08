import { GeoMap } from "../../components/GeoMap";
import { Panel } from "../../components/Panel";
import type { GymOutV2 } from "../../lib/api";

type GeoCanvasPanelProps = {
  gyms: GymOutV2[];
  selectedGymId: string | null;
  onSelectGym: (gymId: string) => void;
  nearbyLat?: number;
  nearbyLon?: number;
};

export function GeoCanvasPanel(props: GeoCanvasPanelProps) {
  return (
    <Panel
      title="Geo Canvas"
      subtitle="A live coordinate projection of the current result set with selectable gym pins."
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
