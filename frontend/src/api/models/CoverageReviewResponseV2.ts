/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CoverageReviewSummaryV2 } from './CoverageReviewSummaryV2';
import type { GymOutV2 } from './GymOutV2';
export type CoverageReviewResponseV2 = {
    api_version?: string;
    region: string;
    count: number;
    summary: CoverageReviewSummaryV2;
    results: Array<GymOutV2>;
};

