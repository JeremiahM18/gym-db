/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InferenceMeta } from './InferenceMeta';
import type { InferenceResult } from './InferenceResult';
import type { SourceProvenanceV2 } from './SourceProvenanceV2';
/**
 * v2 Gym representation.
 *
 * Changes from v1:
 * - inference is fully structured
 * - norm_name is optional (internal detail)
 * - tags can be omitted by clients
 */
export type GymOutV2 = {
    id: string;
    name: string;
    norm_name: string;
    lat: number;
    lon: number;
    confidence_score?: (number | null);
    osm_refs: Array<Record<string, any>>;
    tags?: (Record<string, any> | null);
    inference: Record<string, InferenceResult>;
    inference_meta: InferenceMeta;
    source_provenance: SourceProvenanceV2;
    inference_summary?: (Record<string, string> | null);
};

