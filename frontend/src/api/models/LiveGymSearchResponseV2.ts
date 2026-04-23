/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LiveGymOutV2 } from './LiveGymOutV2';
import type { LiveSearchOriginV2 } from './LiveSearchOriginV2';
export type LiveGymSearchResponseV2 = {
    api_version?: string;
    query: string;
    place_query: string;
    search_id: string;
    status: string;
    enrichment_status: string;
    revision: number;
    updated_at: string;
    expires_at: string;
    poll_after_ms?: (number | null);
    count: number;
    radius_m: number;
    origin: LiveSearchOriginV2;
    results: Array<LiveGymOutV2>;
};

