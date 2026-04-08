import type { Dispatch, FormEvent, SetStateAction } from "react";

import { Panel } from "../../components/Panel";
import {
  specialtyOptions,
  tierOptions,
  type FiltersState,
  type NearbyState,
  type ToggleChoice,
} from "./types";
import { titleCase } from "./utils";

type QueryControlsPanelProps = {
  filters: FiltersState;
  nearby: NearbyState;
  loading: boolean;
  nearbyRadiusLabel: string;
  onCatalogSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onNearbySubmit: (event: FormEvent<HTMLFormElement>) => void;
  setFilters: Dispatch<SetStateAction<FiltersState>>;
  setNearby: Dispatch<SetStateAction<NearbyState>>;
};

export function QueryControlsPanel(props: QueryControlsPanelProps) {
  return (
    <Panel
      title="Query Controls"
      subtitle="Run catalog filters or nearby search against the live backend."
      accent="Read Surface"
    >
      <form className="controls-grid" onSubmit={props.onCatalogSubmit}>
        <label>
          <span>Region</span>
          <input
            value={props.filters.region}
            onChange={(event) =>
              props.setFilters((current) => ({ ...current, region: event.target.value }))
            }
            placeholder="default region"
          />
        </label>
        <label>
          <span>Min confidence</span>
          <input
            value={props.filters.minConf}
            onChange={(event) =>
              props.setFilters((current) => ({ ...current, minConf: event.target.value }))
            }
            inputMode="decimal"
          />
        </label>
        <label>
          <span>Tier</span>
          <select
            value={props.filters.tier}
            onChange={(event) =>
              props.setFilters((current) => ({ ...current, tier: event.target.value }))
            }
          >
            <option value="">Any</option>
            {tierOptions.map((tier) => (
              <option key={tier} value={tier}>
                {titleCase(tier)}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Specialty</span>
          <select
            value={props.filters.specialty}
            onChange={(event) =>
              props.setFilters((current) => ({ ...current, specialty: event.target.value }))
            }
          >
            <option value="">Any</option>
            {specialtyOptions.map((specialty) => (
              <option key={specialty} value={specialty}>
                {titleCase(specialty)}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Lifter friendly</span>
          <select
            value={props.filters.lifterFriendly}
            onChange={(event) =>
              props.setFilters((current) => ({
                ...current,
                lifterFriendly: event.target.value as ToggleChoice,
              }))
            }
          >
            <option value="any">Any</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </label>
        <label>
          <span>24/7</span>
          <select
            value={props.filters.is247}
            onChange={(event) =>
              props.setFilters((current) => ({
                ...current,
                is247: event.target.value as ToggleChoice,
              }))
            }
          >
            <option value="any">Any</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </label>
        <label>
          <span>Result limit</span>
          <input
            value={props.filters.limit}
            onChange={(event) =>
              props.setFilters((current) => ({ ...current, limit: event.target.value }))
            }
            inputMode="numeric"
          />
        </label>
        <div className="controls-actions">
          <button className="primary-button" type="submit" disabled={props.loading}>
            Refresh catalog
          </button>
        </div>
      </form>

      <form className="controls-grid nearby-grid" onSubmit={props.onNearbySubmit}>
        <label>
          <span>Latitude</span>
          <input
            value={props.nearby.lat}
            onChange={(event) =>
              props.setNearby((current) => ({ ...current, lat: event.target.value }))
            }
            inputMode="decimal"
          />
        </label>
        <label>
          <span>Longitude</span>
          <input
            value={props.nearby.lon}
            onChange={(event) =>
              props.setNearby((current) => ({ ...current, lon: event.target.value }))
            }
            inputMode="decimal"
          />
        </label>
        <label>
          <span>Radius (meters)</span>
          <input
            value={props.nearby.radiusM}
            onChange={(event) =>
              props.setNearby((current) => ({ ...current, radiusM: event.target.value }))
            }
            inputMode="numeric"
          />
          <small className="field-hint">About {props.nearbyRadiusLabel}</small>
        </label>
        <div className="controls-actions">
          <button className="secondary-button" type="submit" disabled={props.loading}>
            Run nearby search
          </button>
        </div>
      </form>
    </Panel>
  );
}
