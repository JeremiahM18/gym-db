export type Mode = "published" | "live";
export type ToggleChoice = "any" | "yes" | "no";

export type FiltersState = {
  region: string;
  minConf: string;
  tier: string;
  specialty: string;
  lifterFriendly: ToggleChoice;
  is247: ToggleChoice;
  limit: string;
};

export type LiveSearchState = {
  query: string;
  placeQuery: string;
  radiusMiles: string;
  resolvedLabel: string;
};

export type LiveSearchSessionState = {
  searchId: string;
  status: string;
  enrichmentStatus: string;
  revision: number;
  updatedAt: string;
  expiresAt: string;
  pollAfterMs: number | null;
};

export type ActionLink = {
  label: string;
  href: string;
  tone?: "warm" | "cool" | "ink";
};

export type BrowserGym = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  address: string | null;
  cityState: string;
  specialty: string | null;
  tier: string | null;
  confidenceScore: number | null;
  website: string | null;
  phone: string | null;
  email: string | null;
  openingHours: string | null;
  is247: boolean | null;
  lifterFriendly: boolean | null;
  amenityChips: string[];
  distanceM: number | null;
  sourceKind: "published" | "live";
  sourceLabel: string;
  inferenceEngine: string | null;
  rawPublishedGymId?: string;
};

export const specialtyOptions = [
  "general_fitness",
  "crossfit",
  "powerlifting",
  "olympic_weightlifting",
  "bodybuilding",
  "boxing",
  "martial_arts",
  "yoga",
  "climbing",
] as const;

export const tierOptions = ["basic", "mid", "premium"] as const;

export const defaultFilters: FiltersState = {
  region: "",
  minConf: "0.3",
  tier: "",
  specialty: "",
  lifterFriendly: "any",
  is247: "any",
  limit: "100",
};

export const defaultLiveSearch: LiveSearchState = {
  query: "gym",
  placeQuery: "Nashville, TN",
  radiusMiles: "10",
  resolvedLabel: "",
};
