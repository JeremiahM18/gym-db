/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GeocodeResponseV2 } from '../models/GeocodeResponseV2';
import type { GymEmbeddingV2 } from '../models/GymEmbeddingV2';
import type { GymResponseV2 } from '../models/GymResponseV2';
import type { GymsListResponseV2 } from '../models/GymsListResponseV2';
import type { GymsNearbyResponseV2 } from '../models/GymsNearbyResponseV2';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GymsService {
    /**
     * Nearby Gyms
     * Find gyms near a geographic point.
     * Uses PostGIS for distance calculations.
     * @param lat
     * @param lon
     * @param radiusM
     * @param limit
     * @returns GymsNearbyResponseV2 Successful Response
     * @throws ApiError
     */
    public static nearbyGymsV2GymsGeoNearbyGet(
        lat: number,
        lon: number,
        radiusM: number = 1000,
        limit: number = 50,
    ): CancelablePromise<GymsNearbyResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/gyms/geo/nearby',
            query: {
                'lat': lat,
                'lon': lon,
                'radius_m': radiusM,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Gyms V2
     * @param region
     * @param minConf
     * @param tier
     * @param specialty
     * @param lifterFriendly
     * @param is247
     * @param lat
     * @param lon
     * @param radiusM
     * @param limit
     * @param offset
     * @returns GymsListResponseV2 Successful Response
     * @throws ApiError
     */
    public static listGymsV2V2GymsGet(
        region?: (string | null),
        minConf?: (number | null),
        tier?: (string | null),
        specialty?: (string | null),
        lifterFriendly?: (boolean | null),
        is247?: (boolean | null),
        lat?: (number | null),
        lon?: (number | null),
        radiusM?: (number | null),
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<GymsListResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/gyms',
            query: {
                'region': region,
                'min_conf': minConf,
                'tier': tier,
                'specialty': specialty,
                'lifter_friendly': lifterFriendly,
                'is_24_7': is247,
                'lat': lat,
                'lon': lon,
                'radius_m': radiusM,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Geocode Location V2
     * @param q City, neighborhood, or place name
     * @param limit
     * @returns GeocodeResponseV2 Successful Response
     * @throws ApiError
     */
    public static geocodeLocationV2V2GeocodeGet(
        q: string,
        limit: number = 5,
    ): CancelablePromise<GeocodeResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/geocode',
            query: {
                'q': q,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Gym Embeddings V2
     * @param region
     * @returns GymEmbeddingV2 Successful Response
     * @throws ApiError
     */
    public static listGymEmbeddingsV2V2GymsEmbeddingsGet(
        region?: (string | null),
    ): CancelablePromise<Array<GymEmbeddingV2>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/gyms/embeddings',
            query: {
                'region': region,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Gym V2
     * @param gymId
     * @param region
     * @returns GymResponseV2 Successful Response
     * @throws ApiError
     */
    public static getGymV2V2GymsGymIdGet(
        gymId: string,
        region?: (string | null),
    ): CancelablePromise<GymResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/gyms/{gym_id}',
            path: {
                'gym_id': gymId,
            },
            query: {
                'region': region,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
