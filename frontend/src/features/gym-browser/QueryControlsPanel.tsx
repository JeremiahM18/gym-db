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

const LIVE_RADIUS_PRESETS_MILES = [1, 3, 5, 10, 15, 25] as const;

type QueryControlsPanelProps = {
  filters: FiltersState;
  liveSearch: LiveSearchState;
  loading: boolean;
  liveRadiusLabel: string;
  liveSearchSummary: string;
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
        <div className="live-search-summary">
          <span className="live-search-summary-label">Live Search</span>
          <strong>{props.liveSearchSummary}</strong>
          <p>
            Search the real world by place and radius. GymDB handles the coordinates behind the
            scenes so the user experience stays human.
          </p>
        </div>
        <label>
          <span>What are you looking for?</span>
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
            Leave it as <strong>gym</strong> for a broad search, or type something more specific
            like <strong>crossfit</strong>, <strong>pilates</strong>, or a brand name.
          </small>
        </label>
        <label>
          <span>Near</span>
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
            Required. Pick the city, neighborhood, or place you want GymDB to search around.
          </small>
        </label>
        <label>
          <span>Within</span>
          <input
            value={props.liveSearch.radiusMiles}
            onChange={(event) =>
              props.setLiveSearch((current) => ({
                ...current,
                radiusMiles: event.target.value,
              }))
            }
            inputMode="decimal"
            placeholder="10"
          />
          <small className="field-hint">
            Miles from the chosen place. Current search area: about {props.liveRadiusLabel}.
          </small>
        </label>
        <div className="radius-preset-row" role="group" aria-label="Radius quick picks">
          {LIVE_RADIUS_PRESETS_MILES.map((presetMiles) => {
            const presetValue = String(presetMiles);
            const active = props.liveSearch.radiusMiles === presetValue;

            return (
              <button
                key={presetMiles}
                className={active ? "chip active" : "chip"}
                type="button"
                onClick={() =>
                  props.setLiveSearch((current) => ({
                    ...current,
                    radiusMiles: presetValue,
                  }))
                }
              >
                {presetMiles} mi
              </button>
            );
          })}
        </div>
        {props.liveSearch.resolvedLabel ? (
          <div className="field-hint live-origin-note">
            Last resolved search origin: {props.liveSearch.resolvedLabel} within{" "}
            {props.liveRadiusLabel}.
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
