/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InferenceEmbeddingV2 } from './InferenceEmbeddingV2';
/**
 * Embedding-ready representation of a gym.
 * Safe for vector databases and LLM pipelines.
 */
export type GymEmbeddingV2 = {
    id: string;
    name: string;
    region: string;
    /**
     * Determininstic text used for vector embeddings
     */
    embedding_text: string;
    inference: Array<InferenceEmbeddingV2>;
    confidence_score?: (number | null);
    lat?: (number | null);
    lon?: (number | null);
};

