/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GymOutV2 } from './GymOutV2';
export type GymsListResponseV2 = {
    api_version?: string;
    region: string;
    count: number;
    has_more?: boolean;
    results: Array<GymOutV2>;
};

