import type { Dispatch, FormEvent, SetStateAction } from "react";

import { Panel } from "../../components/Panel";
import {
  specialtyOptions,
  tierOptions,
  type LiveSearchState,
  type FiltersState,
  type ToggleChoice,
} from "./types";
import { titleCase } from "./utils";

type QueryControlsPanelProps = {
  filters: FiltersState;
  liveSearch: LiveSearchState;
  loading: boolean;
  liveRadiusLabel: string;
  onPublishedSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onLiveSubmit: (event: FormEvent<HTMLFormElement>) => void;
  setFilters: Dispatch<SetStateAction<FiltersState>>;
  setLiveSearch: Dispatch<SetStateAction<LiveSearchState>>;
};

export function QueryControlsPanel(props: QueryControlsPanelProps) {
  return (
    <Panel
      title="Query Controls"
      subtitle="Browse the published catalog or run a true live world search without exposing coordinates."
      accent="Search Surface"
    >
      <form className="controls-grid" onSubmit={props.onPublishedSubmit}>
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
            Refresh published catalog
          </button>
        </div>
      </form>

      <form className="controls-grid nearby-grid" onSubmit={props.onLiveSubmit}>
        <label>
          <span>Gym search</span>
          <input
            value={props.liveSearch.query}
            onChange={(event) =>
              props.setLiveSearch((current) => ({
                ...current,
                query: event.target.value,
              }))
            }
            placeholder="gym, crossfit, powerlifting, equinox"
          />
          <small className="field-hint">
            Leave it as <strong>gym</strong> for a broad live search, or search for a specific
            brand or specialty.
          </small>
        </label>
        <label>
          <span>City, neighborhood, or place</span>
          <input
            value={props.liveSearch.placeQuery}
            onChange={(event) =>
              props.setLiveSearch((current) => ({
                ...current,
                placeQuery: event.target.value,
                resolvedLabel: "",
              }))
            }
            placeholder="Nashville, TN"
          />
          <small className="field-hint">
            Required. GymDB resolves this place with TomTom, then runs the live search around it.
          </small>
        </label>
        <label>
          <span>Radius (meters)</span>
          <input
            value={props.liveSearch.radiusM}
            onChange={(event) =>
              props.setLiveSearch((current) => ({ ...current, radiusM: event.target.value }))
            }
            inputMode="numeric"
          />
          <small className="field-hint">About {props.liveRadiusLabel}</small>
        </label>
        {props.liveSearch.resolvedLabel ? (
          <div className="field-hint">
            Live search origin: {props.liveSearch.resolvedLabel}
          </div>
        ) : null}
        <div className="controls-actions">
          <button className="secondary-button" type="submit" disabled={props.loading}>
            Run live search
          </button>
        </div>
      </form>
    </Panel>
  );
}
