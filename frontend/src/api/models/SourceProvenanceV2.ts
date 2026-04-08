/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SourceReferenceV2 } from './SourceReferenceV2';
export type SourceProvenanceV2 = {
    primary?: string;
    confirmed_by?: Array<string>;
    match_status?: string;
    external_refs?: Record<string, SourceReferenceV2>;
};

