import type { Dispatch, FormEvent, SetStateAction } from "react";

import { Panel } from "../../components/Panel";
import {
  specialtyOptions,
  tierOptions,
  type LiveSearchState,
  type FiltersState,
  type Mode,
  type ToggleChoice,
} from "./types";
import { titleCase } from "./utils";

const LIVE_RADIUS_PRESETS_MILES = [1, 3, 5, 10, 25, 50, 100] as const;

type QueryControlsPanelProps = {
  mode: Mode;
  filters: FiltersState;
  liveSearch: LiveSearchState;
  loading: boolean;
  liveRadiusLabel: string;
  liveSearchSummary: string;
  onModeChange: (mode: Mode) => void;
  onPublishedSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onLiveSubmit: (event: FormEvent<HTMLFormElement>) => void;
  setFilters: Dispatch<SetStateAction<FiltersState>>;
  setLiveSearch: Dispatch<SetStateAction<LiveSearchState>>;
};

function getQualityPreset(minConf: string) {
  const value = Number(minConf);
  if (!Number.isFinite(value) || value <= 0.3) {
    return "all";
  }
  if (value <= 0.65) {
    return "reviewed";
  }
  return "strongest";
}

function getMinConfForPreset(preset: string) {
  switch (preset) {
    case "reviewed":
      return "0.6";
    case "strongest":
      return "0.8";
    default:
      return "0.3";
  }
}

export function QueryControlsPanel(props: QueryControlsPanelProps) {
  return (
    <Panel
      title="Search"
      subtitle="Start with a place and radius. Use curated picks when you want a tighter shortlist after exploring."
      accent="Find Gyms"
    >
      <div className="search-intro">
        <strong>
          {props.mode === "live"
            ? "Nearby search is the main way to explore a city."
            : "Curated picks is the tighter follow-up view."}
        </strong>
        <p>
          {props.mode === "live"
            ? "Pick a place, set a radius, and compare gyms by distance, amenities, and fit."
            : "Use curated picks when you want a cleaner, more selective pass after exploring the broader area."}
        </p>
      </div>
      <div className="source-switcher" role="group" aria-label="Search view">
        <button
          className={props.mode === "live" ? "chip active" : "chip"}
          type="button"
          onClick={() => props.onModeChange("live")}
        >
          Nearby search
        </button>
        <button
          className={props.mode === "published" ? "chip active" : "chip"}
          type="button"
          onClick={() => props.onModeChange("published")}
        >
          Curated picks
        </button>
      </div>

      {props.mode === "live" ? (
        <form className="controls-grid live-search-form" onSubmit={props.onLiveSubmit}>
          <div className="live-search-summary">
            <span className="live-search-summary-label">Live Search</span>
            <strong>{props.liveSearchSummary}</strong>
            <p>
              Search around any city, neighborhood, or landmark and see nearby gyms ordered by
              distance.
            </p>
          </div>
          <label>
            <span>Gym type or brand</span>
            <input
              value={props.liveSearch.query}
              onChange={(event) =>
                props.setLiveSearch((current) => ({
                  ...current,
                  query: event.target.value,
                }))
              }
              placeholder="gym, crossfit, powerlifting, pilates"
            />
            <small className="field-hint">
              Keep <strong>gym</strong> for a broad search, or get more specific with a style,
              amenity, or brand.
            </small>
          </label>
          <label>
            <span>Place</span>
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
              Try a city, neighborhood, ZIP code, or landmark.
            </small>
          </label>
          <label>
            <span>Radius</span>
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
              Search within about {props.liveRadiusLabel} of the place you picked.
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
              Searching around {props.liveSearch.resolvedLabel}.
            </div>
          ) : null}
          <div className="controls-actions">
            <button className="secondary-button" type="submit" disabled={props.loading}>
              Find nearby gyms
            </button>
          </div>
        </form>
      ) : (
        <form className="controls-grid published-search-form" onSubmit={props.onPublishedSubmit}>
          <div className="live-search-summary catalog-summary">
            <span className="live-search-summary-label">Curated GymDB View</span>
            <strong>Compare the tighter shortlist</strong>
            <p>
              Use curated picks when you want a cleaner review of the current catalog instead of
              the broader nearby search.
            </p>
          </div>
          <label>
            <span>Listing quality</span>
            <select
              value={getQualityPreset(props.filters.minConf)}
              onChange={(event) =>
                props.setFilters((current) => ({
                  ...current,
                  minConf: getMinConfForPreset(event.target.value),
                }))
              }
            >
              <option value="all">Everything in the catalog</option>
              <option value="reviewed">More reviewed listings</option>
              <option value="strongest">Only the strongest matches</option>
            </select>
          </label>
          <label>
            <span>Gym style</span>
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
            <span>Price tier</span>
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
            <span>Lifter-friendly</span>
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
            <span>Open 24/7</span>
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
            <span>Show</span>
            <select
              value={props.filters.limit}
              onChange={(event) =>
                props.setFilters((current) => ({ ...current, limit: event.target.value }))
              }
            >
              <option value="25">25 gyms</option>
              <option value="50">50 gyms</option>
              <option value="100">100 gyms</option>
            </select>
          </label>
          <div className="controls-actions">
            <button className="primary-button" type="submit" disabled={props.loading}>
              Show curated gyms
            </button>
          </div>
        </form>
      )}
    </Panel>
  );
}
