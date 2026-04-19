export type Mode = "catalog" | "nearby";
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

export type NearbyState = {
  placeQuery: string;
  lat: string;
  lon: string;
  radiusM: string;
  resolvedLabel: string;
};

export type ActionLink = {
  label: string;
  href: string;
  tone?: "warm" | "cool" | "ink";
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

export const defaultNearby: NearbyState = {
  placeQuery: "Nashville, TN",
  lat: "36.1627",
  lon: "-86.7816",
  radiusM: "2500",
  resolvedLabel: "",
};
