/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HealthService {
    /**
     * Healthz
     * Liveness probe.
     *
     * Confirms the service process is running.
     * Does NOT check external dependencies.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static healthzHealthzGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/healthz',
        });
    }
    /**
     * Readyz
     * Readiness probe.
     *
     * Confirms external dependencies (DB + extension + schema) are available.
     *
     * Returns 503 when NOT ready.
     *
     * 503 responses are returned using the global error envelope:
     *
     * {
         * "error": {
             * "code": 503,
             * "message": {
                 * "ready": false,
                 * "checks": {...}
                 * }
                 * }
                 * }
                 * @returns any Successful Response
                 * @throws ApiError
                 */
                public static readyzReadyzGet(): CancelablePromise<any> {
                    return __request(OpenAPI, {
                        method: 'GET',
                        url: '/readyz',
                    });
                }
            }
