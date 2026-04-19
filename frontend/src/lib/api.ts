import { ApiError, CancelError, OpenAPI } from "../api";
import type { CancelablePromise } from "../api";
import type { GeocodeResponseV2 } from "../api/models/GeocodeResponseV2";
import type { GymOutV2 } from "../api/models/GymOutV2";
import type { GymResponseV2 } from "../api/models/GymResponseV2";
import type { GymsListResponseV2 } from "../api/models/GymsListResponseV2";
import type { LiveGymOutV2 } from "../api/models/LiveGymOutV2";
import type { LiveGymSearchResponseV2 } from "../api/models/LiveGymSearchResponseV2";
import { GeocodeService } from "../api/services/GeocodeService";
import { GymsService } from "../api/services/GymsService";
import { HealthService } from "../api/services/HealthService";
import { LiveSearchService } from "../api/services/LiveSearchService";

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

type HealthSnapshot = {
  live: boolean;
  ready: boolean;
  readinessPayload: unknown;
  readinessSummary: string;
  readinessHint: string | null;
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

function summarizeReadiness(payload: unknown): {
  summary: string;
  hint: string | null;
} {
  if (!payload || typeof payload !== "object") {
    return {
      summary: "readiness unknown",
      hint: "Published dataset browsing may still work while readiness is degraded.",
    };
  }

  const record = payload as Record<string, unknown>;
  const checks =
    "checks" in record && typeof record.checks === "object" && record.checks !== null
      ? (record.checks as Record<string, unknown>)
      : null;

  if (!checks) {
    return {
      summary: "readiness unknown",
      hint: "Published dataset browsing may still work while readiness is degraded.",
    };
  }

  const failingChecks = Object.entries(checks)
    .filter(([, value]) => value === false)
    .map(([key]) => key);

  if (!failingChecks.length) {
    return {
      summary: "all readiness checks passing",
      hint: null,
    };
  }

  if (failingChecks.length === 1 && failingChecks[0] === "database") {
    return {
      summary: "database unavailable",
      hint: "Catalog browsing can still work from the published dataset while DB readiness is failing.",
    };
  }

  return {
    summary: `checks failing: ${failingChecks.join(", ")}`,
    hint: "Catalog browsing can still work from the published dataset while readiness is degraded.",
  };
}

function extractReadinessFailure(error: unknown): unknown {
  if (error instanceof ApiError) {
    const body = error.body as
      | { error?: { message?: unknown } }
      | undefined;
    if (body?.error?.message !== undefined) {
      return body.error.message;
    }
  }

  return extractErrorMessage(error, "Readiness request failed");
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
  filters: Required<Pick<GymFilters, "lat" | "lon" | "radiusM">> & GymFilters,
  signal?: AbortSignal,
): Promise<GymsListResponseV2> {
  return listGyms(filters, signal);
}

export async function liveSearchGyms(
  place: string,
  query: string,
  radiusM: number,
  signal?: AbortSignal,
): Promise<LiveGymSearchResponseV2> {
  return bindAbort(
    LiveSearchService.liveSearchGymsV2V2LiveSearchGet(place, query, radiusM),
    signal,
  );
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
        payload: extractReadinessFailure(error),
      })),
  ]);

  try {
    const readiness = summarizeReadiness(readinessPayload.payload);
    return {
      live: liveResponse,
      ready: readinessPayload.ok,
      readinessPayload: readinessPayload.payload,
      readinessSummary: readinessPayload.ok ? "all readiness checks passing" : readiness.summary,
      readinessHint: readinessPayload.ok ? null : readiness.hint,
    };
  } catch {
    return {
      live: liveResponse,
      ready: false,
      readinessPayload: null,
      readinessSummary: "readiness unknown",
      readinessHint: "Published dataset browsing may still work while readiness is degraded.",
    };
  }
}

export type {
  GeocodeResponseV2,
  GymFilters,
  GymOutV2,
  HealthSnapshot,
  LiveGymOutV2,
  LiveGymSearchResponseV2,
};
