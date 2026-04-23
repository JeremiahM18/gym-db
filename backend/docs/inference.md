# Inference Contract

Status: **stable**

This document defines the public guarantees of GymDB inference. It describes the output contract and invariants, not the implementation details of the rule engine.

## Purpose

Inference derives structured attributes from stored gym facts while remaining:

- deterministic
- explainable
- auditable
- safe to rerun

Inference does not mutate stored facts and does not depend on external runtime state.

## Output Shape

Each emitted inference result has this shape:

```json
{
  "value": "<bool | int | string>",
  "confidence": 0.0,
  "reasons": ["..."],
  "source": "rule"
}
```

Field meanings:

- `value`
  The inferred value. GymDB currently emits `bool`, `int`, or `string` values.

- `confidence`
  Strength of evidence, not probability of correctness.

- `reasons`
  Human-readable explanations for the inference decision.

- `source`
  The inference source identifier. The current rule engine emits `"rule"`.

## Invariants

- emitted inference entries are structurally complete
- identical inputs produce identical outputs
- `reasons` ordering is stable
- inference keys may be absent when GymDB chooses not to emit a result
- emitted values must be explainable by their reasons

## Confidence Semantics

Confidence is a calibration signal for evidence strength.

Typical interpretation:

- `0.90-1.00` explicit high-confidence signals
- `0.60-0.89` strong heuristic signals
- `0.30-0.59` weak or partial signals
- `0.00-0.29` default or low-information signals

## Compatibility

Allowed without a version bump:

- adding new inference attributes
- improving calibration
- adding additional reasons

Require a version bump:

- changing the meaning of an existing inference value
- removing an existing inference attribute
- changing the meaning of confidence

## Enforcement

The contract is protected by backend tests, API contract coverage, and typed models. If implementation and documentation diverge, the implementation is wrong or the documentation is stale; both cases should be treated as defects.
