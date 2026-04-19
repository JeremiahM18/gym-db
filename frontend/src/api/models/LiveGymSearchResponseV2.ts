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
    count: number;
    radius_m: number;
    origin: LiveSearchOriginV2;
    results: Array<LiveGymOutV2>;
};

