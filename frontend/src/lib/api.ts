import { CancelError, OpenAPI } from "../api";
import type { CancelablePromise } from "../api";
import type { GeocodeResponseV2 } from "../api/models/GeocodeResponseV2";
import type { GymOutV2 } from "../api/models/GymOutV2";
import type { GymResponseV2 } from "../api/models/GymResponseV2";
import type { GymsListResponseV2 } from "../api/models/GymsListResponseV2";
import { GeocodeService } from "../api/services/GeocodeService";
import { GymsService } from "../api/services/GymsService";
import { HealthService } from "../api/services/HealthService";

OpenAPI.BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
OpenAPI.TOKEN = import.meta.env.VITE_API_TOKEN;

type GymFilters = {
  region?: string;
  minConf?: number;
  tier?: string;
  specialty?: string;
  lifterFriendly?: boolean;
  is247?: boolean;
  lat?: number;
  lon?: number;
  radiusM?: number;
  limit?: number;
  offset?: number;
};

type NearbyFilters = Required<Pick<GymFilters, "lat" | "lon" | "radiusM">> & GymFilters;

type HealthSnapshot = {
  live: boolean;
  ready: boolean;
  readinessPayload: unknown;
};

function bindAbort<T>(
  promise: CancelablePromise<T>,
  signal?: AbortSignal,
): Promise<T> {
  if (!signal) {
    return promise;
  }

  if (signal.aborted) {
    promise.cancel();
  } else {
    signal.addEventListener("abort", () => promise.cancel(), { once: true });
  }

  return promise.catch((error: unknown) => {
    if (error instanceof CancelError && signal.aborted) {
      throw new DOMException("Request aborted", "AbortError");
    }
    throw error;
  });
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

export async function listGyms(
  filters: GymFilters,
  signal?: AbortSignal,
): Promise<GymsListResponseV2> {
  return bindAbort(
    GymsService.listGymsV2V2GymsGet(
      filters.region,
      filters.minConf,
      filters.tier,
      filters.specialty,
      filters.lifterFriendly,
      filters.is247,
      filters.lat,
      filters.lon,
      filters.radiusM,
      filters.limit ?? 100,
      filters.offset,
    ),
    signal,
  );
}

export async function searchPublishedNearbyGyms(
  filters: NearbyFilters,
  signal?: AbortSignal,
): Promise<GymsListResponseV2> {
  return listGyms(filters, signal);
}

export async function geocodeLocation(
  query: string,
  signal?: AbortSignal,
): Promise<GeocodeResponseV2> {
  return bindAbort(GeocodeService.geocodeLocationV2V2GeocodeGet(query), signal);
}

export async function getGym(
  gymId: string,
  region?: string,
  signal?: AbortSignal,
): Promise<GymResponseV2> {
  return bindAbort(GymsService.getGymV2V2GymsGymIdGet(gymId, region), signal);
}

export async function getHealth(signal?: AbortSignal): Promise<HealthSnapshot> {
  const [liveResponse, readinessPayload] = await Promise.all([
    bindAbort(HealthService.healthzHealthzGet(), signal)
      .then(() => true)
      .catch(() => false),
    bindAbort(HealthService.readyzReadyzGet(), signal)
      .then((payload) => ({ ok: true, payload }))
      .catch((error: unknown) => ({
        ok: false,
        payload: extractErrorMessage(error, "Readiness request failed"),
      })),
  ]);

  try {
    return {
      live: liveResponse,
      ready: readinessPayload.ok,
      readinessPayload: readinessPayload.payload,
    };
  } catch {
    return {
      live: liveResponse,
      ready: false,
      readinessPayload: null,
    };
  }
}

export type { GeocodeResponseV2, GymFilters, GymOutV2, HealthSnapshot, NearbyFilters };
