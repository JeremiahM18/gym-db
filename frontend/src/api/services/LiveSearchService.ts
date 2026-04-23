/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LiveGymSearchResponseV2 } from '../models/LiveGymSearchResponseV2';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LiveSearchService {
    /**
     * Live Search Gyms V2
     * @param place City, neighborhood, or place
     * @param q Gym name, brand, or search term. Defaults to gym.
     * @param radiusM
     * @param limit
     * @returns LiveGymSearchResponseV2 Successful Response
     * @throws ApiError
     */
    public static liveSearchGymsV2V2LiveSearchGet(
        place: string,
        q: string = 'gym',
        radiusM: number = 25000,
        limit: number = 25,
    ): CancelablePromise<LiveGymSearchResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/live/search',
            query: {
                'place': place,
                'q': q,
                'radius_m': radiusM,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Live Search Session V2
     * @param searchId
     * @returns LiveGymSearchResponseV2 Successful Response
     * @throws ApiError
     */
    public static getLiveSearchSessionV2V2LiveSearchSearchIdGet(
        searchId: string,
    ): CancelablePromise<LiveGymSearchResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/live/search/{search_id}',
            path: {
                'search_id': searchId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
