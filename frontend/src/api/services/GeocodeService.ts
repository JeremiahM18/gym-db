/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GeocodeResponseV2 } from '../models/GeocodeResponseV2';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GeocodeService {
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
}
