/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CoverageReviewResponseV2 } from '../models/CoverageReviewResponseV2';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReviewService {
    /**
     * Coverage Review V2
     * @param region
     * @param status
     * @param maxConf
     * @param contradictionsOnly
     * @param limit
     * @param offset
     * @returns CoverageReviewResponseV2 Successful Response
     * @throws ApiError
     */
    public static coverageReviewV2V2ReviewCoverageGet(
        region?: (string | null),
        status?: (string | null),
        maxConf?: (number | null),
        contradictionsOnly: boolean = false,
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<CoverageReviewResponseV2> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/v2/review/coverage',
            query: {
                'region': region,
                'status': status,
                'max_conf': maxConf,
                'contradictions_only': contradictionsOnly,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
