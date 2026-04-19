import type { GymFilters, GymOutV2 } from "../../lib/api";
import type { LiveGymOutV2 } from "../../lib/api";
import type { ActionLink, BrowserGym, FiltersState, ToggleChoice } from "./types";

const METERS_PER_MILE = 1609.344;
const EARTH_RADIUS_METERS = 6_371_000;

type MapBounds = {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
  latSpan: number;
  lonSpan: number;
};

export type MapPoint = {
  gym: BrowserGym;
  x: number;
  y: number;
  distanceLabel: string | null;
};

export function choiceToBoolean(choice: ToggleChoice): boolean | undefined {
  if (choice === "yes") {
    return true;
  }
  if (choice === "no") {
    return false;
  }
  return undefined;
}

export function parseNumber(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function buildGymFilters(filters: FiltersState): GymFilters {
  return {
    region: filters.region || undefined,
    minConf: parseNumber(filters.minConf),
    tier: filters.tier || undefined,
    specialty: filters.specialty || undefined,
    lifterFriendly: choiceToBoolean(filters.lifterFriendly),
    is247: choiceToBoolean(filters.is247),
    limit: parseNumber(filters.limit) ?? 100,
    offset: 0,
  };
}

export function formatConfidence(value: number | null | undefined): string {
  if (value == null) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

export function titleCase(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function inferString(gym: GymOutV2, key: string, fallback = "Unknown"): string {
  const result = gym.inference[key];
  return result ? String(result.value) : fallback;
}

export function inferBoolean(gym: GymOutV2, key: string): string {
  const result = gym.inference[key];
  if (!result) {
    return "Unknown";
  }
  return result.value ? "Yes" : "No";
}

export function normalizeUrl(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }

  return `https://${trimmed}`;
}

export function getTagValue(gym: GymOutV2, keys: string[]): string | null {
  const tags = gym.tags ?? {};
  for (const key of keys) {
    const value = tags[key];
    if (value == null) {
      continue;
    }

    const normalized = String(value).trim();
    if (normalized) {
      return normalized;
    }
  }

  return null;
}

export function getWebsite(gym: GymOutV2): string | null {
  return normalizeUrl(getTagValue(gym, ["website", "contact:website", "url"]));
}

export function getPhone(gym: GymOutV2): string | null {
  return getTagValue(gym, ["phone", "contact:phone"]);
}

export function getEmail(gym: GymOutV2): string | null {
  return getTagValue(gym, ["email", "contact:email"]);
}

export function getOpeningHours(gym: GymOutV2): string | null {
  return getTagValue(gym, ["opening_hours"]);
}

export function getTomTomRef(
  gym: Pick<GymOutV2, "source_provenance">,
): {
  city?: string | null;
  url?: string | null;
} | null {
  const externalRefs = gym.source_provenance?.external_refs;
  if (!externalRefs || typeof externalRefs !== "object" || !("tomtom" in externalRefs)) {
    return null;
  }
  return externalRefs.tomtom ?? null;
}

export function getAddress(gym: GymOutV2): string | null {
  const tags = gym.tags ?? {};
  const parts = [
    tags["addr:housenumber"],
    tags["addr:street"],
    tags["addr:city"],
    tags["addr:state"],
    tags["addr:postcode"],
  ]
    .filter((part) => part != null && String(part).trim())
    .map((part) => String(part).trim());

  return parts.length ? parts.join(", ") : null;
}

export function getCityState(gym: GymOutV2): string {
  const city = getTagValue(gym, ["addr:city"]);
  const state = getTagValue(gym, ["addr:state"]);

  if (city && state) {
    return `${city}, ${state}`;
  }
  if (city) {
    return city;
  }
  if (state) {
    return state;
  }

  return "City not published";
}

export function buildMapsUrl(gym: Pick<BrowserGym, "lat" | "lon" | "name">): string {
  const query = encodeURIComponent(`${gym.lat},${gym.lon} ${gym.name}`);
  return `https://www.google.com/maps/search/?api=1&query=${query}`;
}

export function buildOsmUrl(gym: Pick<BrowserGym, "lat" | "lon">): string {
  return `https://www.openstreetmap.org/?mlat=${gym.lat}&mlon=${gym.lon}#map=18/${gym.lat}/${gym.lon}`;
}

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

export function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const originLat = toRadians(lat1);
  const targetLat = toRadians(lat2);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(originLat) * Math.cos(targetLat) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_METERS * c;
}

export function formatMilesFromMeters(meters: number): string {
  const miles = meters / METERS_PER_MILE;
  return miles >= 10 ? `${miles.toFixed(0)} mi` : `${miles.toFixed(1)} mi`;
}

export function milesToMeters(miles: number): number {
  return Math.round(miles * METERS_PER_MILE);
}

export function formatMilesValue(miles: number): string {
  if (!Number.isFinite(miles)) {
    return "n/a";
  }

  return miles >= 10 || Number.isInteger(miles) ? `${miles.toFixed(0)} mi` : `${miles.toFixed(1)} mi`;
}

export function getAmenityChips(gym: GymOutV2): string[] {
  const tags = gym.tags ?? {};
  const amenitySignals: Array<[string, string]> = [
    ["swimming_pool", "Pool"],
    ["sauna", "Sauna"],
    ["shower", "Showers"],
    ["internet_access", "Wi-Fi"],
    ["toilets:wheelchair", "Wheelchair toilets"],
    ["wheelchair", "Wheelchair access"],
    ["opening_hours", "Hours listed"],
    ["website", "Website"],
    ["contact:website", "Website"],
    ["phone", "Phone"],
    ["contact:phone", "Phone"],
  ];

  const chips = new Set<string>();
  for (const [key, label] of amenitySignals) {
    const value = tags[key];
    if (value == null) {
      continue;
    }

    const normalized = String(value).trim().toLowerCase();
    if (!normalized || normalized === "no") {
      continue;
    }
    chips.add(label);
  }

  const specialty = inferString(gym, "specialty", "");
  if (specialty) {
    chips.add(titleCase(specialty));
  }
  if (gym.inference_summary?.premium_score) {
    chips.add(`Premium signal ${gym.inference_summary.premium_score}`);
  }

  return Array.from(chips).slice(0, 8);
}

export function getBounds(gyms: BrowserGym[]): MapBounds {
  const lats = gyms.map((gym) => gym.lat);
  const lons = gyms.map((gym) => gym.lon);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);

  return {
    minLat,
    maxLat,
    minLon,
    maxLon,
    latSpan: Math.max(maxLat - minLat, 0.01),
    lonSpan: Math.max(maxLon - minLon, 0.01),
  };
}

export function buildMapPoints(
  gyms: BrowserGym[],
  mapWidth: number,
  mapHeight: number,
  mapPadding: number,
  nearbyLat?: number,
  nearbyLon?: number,
): MapPoint[] {
  if (!gyms.length) {
    return [];
  }

  const bounds = getBounds(gyms);
  return gyms.map((gym) => {
    const x = mapPadding + ((gym.lon - bounds.minLon) / bounds.lonSpan) * (mapWidth - mapPadding * 2);
    const y = mapPadding + (1 - (gym.lat - bounds.minLat) / bounds.latSpan) * (mapHeight - mapPadding * 2);
    const distanceLabel =
      nearbyLat != null && nearbyLon != null
        ? formatMilesFromMeters(haversineMeters(nearbyLat, nearbyLon, gym.lat, gym.lon))
        : null;

    return { gym, x, y, distanceLabel };
  });
}

export function filterGymsByQuery(gyms: BrowserGym[], query: string): BrowserGym[] {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return gyms;
  }

  return gyms.filter((gym) => {
    const searchable = [
      gym.name,
      gym.cityState,
      gym.address ?? "",
      gym.specialty ?? "",
    ]
      .join(" ")
      .toLowerCase();

    return searchable.includes(normalizedQuery);
  });
}

export function getAverageConfidence(gyms: BrowserGym[]): string {
  if (!gyms.length) {
    return "n/a";
  }

  const average =
    gyms.reduce((sum, gym) => sum + (gym.confidenceScore ?? 0), 0) / gyms.length;
  return `${Math.round(average * 100)}%`;
}

export function getTopSpecialty(gyms: BrowserGym[]): string {
  if (!gyms.length) {
    return "n/a";
  }

  const counts = new Map<string, number>();
  for (const gym of gyms) {
    const specialty = gym.specialty ?? gym.cityState;
    counts.set(specialty, (counts.get(specialty) ?? 0) + 1);
  }

  const topEntry = Array.from(counts.entries()).sort((left, right) => right[1] - left[1])[0];
  return topEntry ? titleCase(topEntry[0]) : "n/a";
}

export function buildSelectedActionLinks(selectedGym: BrowserGym | null): ActionLink[] {
  if (!selectedGym) {
    return [];
  }

  const links: ActionLink[] = [
    { label: "Open in Maps", href: buildMapsUrl(selectedGym), tone: "cool" },
    { label: "Open in OpenStreetMap", href: buildOsmUrl(selectedGym) },
  ];

  const website = selectedGym.website;
  if (website) {
    links.unshift({ label: "Open website", href: website, tone: "warm" });
  }

  const phone = selectedGym.phone;
  if (phone) {
    links.push({ label: "Call gym", href: `tel:${phone.replace(/\s+/g, "")}` });
  }

  const email = selectedGym.email;
  if (email) {
    links.push({ label: "Email gym", href: `mailto:${email}` });
  }

  return links;
}

export function buildPublishedBrowserGym(gym: GymOutV2): BrowserGym {
  return {
    id: gym.id,
    name: gym.name,
    lat: gym.lat,
    lon: gym.lon,
    address: getAddress(gym),
    cityState: getCityState(gym),
    specialty: inferString(gym, "specialty", "general_fitness"),
    tier: inferString(gym, "tier", "unknown"),
    confidenceScore: gym.confidence_score ?? null,
    website: getWebsite(gym),
    phone: getPhone(gym),
    email: getEmail(gym),
    openingHours: getOpeningHours(gym),
    is247: gym.inference.is_24_7 ? Boolean(gym.inference.is_24_7.value) : null,
    lifterFriendly: gym.inference.lifter_friendly
      ? Boolean(gym.inference.lifter_friendly.value)
      : null,
    amenityChips: getAmenityChips(gym),
    distanceM: null,
    sourceKind: "published",
    sourceLabel: "Published catalog",
    inferenceEngine: gym.inference_meta.engine,
    rawPublishedGymId: gym.id,
  };
}

export function buildLiveBrowserGym(gym: LiveGymOutV2): BrowserGym {
  const tomTomRef = getTomTomRef(gym);
  const address = getAddress(gym) ?? tomTomRef?.city ?? null;
  const cityState = getCityState(gym);
  const confirmedByTomTom = (gym.source_provenance.confirmed_by ?? []).includes("tomtom");
  const matchStatus = gym.source_provenance.match_status;
  const amenityChips = getAmenityChips(gym);

  if (confirmedByTomTom) {
    amenityChips.unshift("TomTom verified");
  } else if (matchStatus === "name_mismatch") {
    amenityChips.unshift("TomTom enriched");
  }

  return {
    id: gym.id,
    name: gym.name,
    lat: gym.lat,
    lon: gym.lon,
    address,
    cityState,
    specialty: inferString(gym, "specialty", "") || null,
    tier: inferString(gym, "tier", "") || null,
    confidenceScore: gym.confidence_score ?? null,
    website: getWebsite(gym) ?? normalizeUrl(tomTomRef?.url ?? null),
    phone: getPhone(gym),
    email: getEmail(gym),
    openingHours: getOpeningHours(gym),
    is247: gym.inference.is_24_7 ? Boolean(gym.inference.is_24_7.value) : null,
    lifterFriendly: gym.inference.lifter_friendly
      ? Boolean(gym.inference.lifter_friendly.value)
      : null,
    amenityChips,
    distanceM: gym.distance_m ?? null,
    sourceKind: "live",
    sourceLabel: confirmedByTomTom
      ? "OSM primary · TomTom verified"
      : "OSM primary · TomTom enriched",
    inferenceEngine: gym.inference_meta.engine,
  };
}
