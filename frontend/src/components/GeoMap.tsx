import { useMemo } from "react";

import type { BrowserGym } from "../features/gym-browser/types";
import { buildMapPoints, getBounds } from "../features/gym-browser/utils";

const MAP_WIDTH = 720;
const MAP_HEIGHT = 420;
const MAP_PADDING = 28;

type GeoMapProps = {
  gyms: BrowserGym[];
  selectedGymId: string | null;
  onSelect: (gymId: string) => void;
  nearbyLat?: number;
  nearbyLon?: number;
};

export function GeoMap(props: GeoMapProps) {
  const points = useMemo(
    () => buildMapPoints(props.gyms, MAP_WIDTH, MAP_HEIGHT, MAP_PADDING, props.nearbyLat, props.nearbyLon),
    [props.gyms, props.nearbyLat, props.nearbyLon],
  );

  if (!points.length) {
    return <div className="map-empty">Run a query to populate the geo panel.</div>;
  }

  const bounds = getBounds(props.gyms);

  return (
    <div className="geo-stage">
      <svg viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} className="geo-map" role="img" aria-label="Gym coordinate map">
        <rect x="0" y="0" width={MAP_WIDTH} height={MAP_HEIGHT} rx="28" className="geo-map-bg" />
        {Array.from({ length: 6 }).map((_, index) => {
          const x = MAP_PADDING + index * ((MAP_WIDTH - MAP_PADDING * 2) / 5);
          const y = MAP_PADDING + index * ((MAP_HEIGHT - MAP_PADDING * 2) / 5);

          return (
            <g key={`grid-${index}`}>
              <line x1={x} y1={MAP_PADDING} x2={x} y2={MAP_HEIGHT - MAP_PADDING} className="geo-grid-line" />
              <line x1={MAP_PADDING} y1={y} x2={MAP_WIDTH - MAP_PADDING} y2={y} className="geo-grid-line" />
            </g>
          );
        })}
        {points.map((point) => {
          const selected = point.gym.id === props.selectedGymId;

          return (
            <g key={point.gym.id} className="geo-point-group" onClick={() => props.onSelect(point.gym.id)}>
              {selected ? <circle cx={point.x} cy={point.y} r="13" className="geo-point-halo" /> : null}
              <circle cx={point.x} cy={point.y} r={selected ? 7 : 5} className={selected ? "geo-point selected" : "geo-point"} />
            </g>
          );
        })}
      </svg>
      <div className="geo-legend-row">
        <div className="geo-legend-card">
          <span>Latitude span</span>
          <strong>{bounds.minLat.toFixed(2)} to {bounds.maxLat.toFixed(2)}</strong>
        </div>
        <div className="geo-legend-card">
          <span>Longitude span</span>
          <strong>{bounds.minLon.toFixed(2)} to {bounds.maxLon.toFixed(2)}</strong>
        </div>
        <div className="geo-legend-card">
          <span>Rendered pins</span>
          <strong>{points.length}</strong>
        </div>
      </div>
    </div>
  );
}
