/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GymEmbeddingV2 } from '../models/GymEmbeddingV2';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EmbeddingsService {
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
}
