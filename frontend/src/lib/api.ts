import type { GymNearbyOutV2 } from "../api/models/GymNearbyOutV2";
import type { GymOutV2 } from "../api/models/GymOutV2";
import type { GymResponseV2 } from "../api/models/GymResponseV2";
import type { GymsListResponseV2 } from "../api/models/GymsListResponseV2";
import type { GymsNearbyResponseV2 } from "../api/models/GymsNearbyResponseV2";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type GymFilters = {
  region?: string;
  minConf?: number;
  tier?: string;
  specialty?: string;
  lifterFriendly?: boolean;
  is247?: boolean;
  limit?: number;
  offset?: number;
};

type NearbyFilters = GymFilters & {
  lat: number;
  lon: number;
  radiusM: number;
};

type HealthSnapshot = {
  live: boolean;
  ready: boolean;
  readinessPayload: unknown;
};

function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>) {
  const url = new URL(path, API_BASE);

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === "") {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }

  return url;
}

async function requestJson<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(buildUrl(path, params), {
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function listGyms(
  filters: GymFilters,
  signal?: AbortSignal,
): Promise<GymsListResponseV2> {
  return requestJson<GymsListResponseV2>(
    "/v2/gyms",
    {
      region: filters.region,
      min_conf: filters.minConf,
      tier: filters.tier,
      specialty: filters.specialty,
      lifter_friendly: filters.lifterFriendly,
      is_24_7: filters.is247,
      limit: filters.limit,
      offset: filters.offset,
    },
    signal,
  );
}

export async function nearbyGyms(
  filters: NearbyFilters,
  signal?: AbortSignal,
): Promise<GymsNearbyResponseV2> {
  return requestJson<GymsNearbyResponseV2>(
    "/v2/gyms/geo/nearby",
    {
      lat: filters.lat,
      lon: filters.lon,
      radius_m: filters.radiusM,
      limit: filters.limit,
    },
    signal,
  );
}

export async function getGym(
  gymId: string,
  region?: string,
  signal?: AbortSignal,
): Promise<GymResponseV2> {
  return requestJson<GymResponseV2>(
    `/v2/gyms/${encodeURIComponent(gymId)}`,
    { region },
    signal,
  );
}

export async function getHealth(signal?: AbortSignal): Promise<HealthSnapshot> {
  const livePromise = fetch(buildUrl("/healthz"), { signal });
  const readyPromise = fetch(buildUrl("/readyz"), { signal });

  const [liveResponse, readyResponse] = await Promise.all([livePromise, readyPromise]);

  let readinessPayload: unknown = null;
  try {
    readinessPayload = await readyResponse.json();
  } catch {
    readinessPayload = null;
  }

  return {
    live: liveResponse.ok,
    ready: readyResponse.ok,
    readinessPayload,
  };
}

export type { GymFilters, GymNearbyOutV2, GymOutV2, HealthSnapshot, NearbyFilters };
