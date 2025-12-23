# Inference Contract

> **Contract status: FROZEN (v1)**
> Breaking semantic changes require an explicit version bump and a documented migration note.

This document defines what inference **must** guarantee, not how it is implemented.

Inference behavior is treated as a **stable contract** and is enforced by tests.
Changes to inference semantics must be deliberate, versioned, and auditable.

---

## Purpose

Inference in GymDB enriches raw, stored facts with derived attributes while preserving:
- determinism
- explainability
- auditability
- safe long-term evolution

Inference does not mutate stored facts and does not depend on runtime state.

---

## Inference Output Structure

All inference results are exposed under a structured inference map.

Each inferred attribute MUST conform to the following schema:

```json
{
    "value": <bool | int | string | null>,
    "confidence": <float between 0.0 and 1.0>,
    "reasons": <array of strings>
}
```
### Field Definitions
- `value`
  The inferred value. May be null if the rule cannot confidently infer.
- `confidence`
  A numeric signal representing strength of evidence.
  Confidence is not a probability of correctness.
- `reasons`
  Readable explanations describing why the inference was made.

---

## Inference Invariants (Must Always Hold)
- Every inference result includes:
    - `value`
    - `confidence`
    - `reasons`
- Inference output is deterministic:
    - Identical inputs always produce identical outputs
- Absence of signal does not imply absence of structure:
    - Inference never returns partially-formed or malformed results

These invariants apply regardless of inference outcome.

---

## Determinism Rules

Inference must be deterministic across runs.

This means:
- No randomness
- No dependency on system time
- No dependency on external state
- Stable iteration order when aggregating signals
- Stable formatting and ordering of `reasons`

Determinism is enforced via automated tests.

---

## Confidence Semantics

Confidence represents **strength of evidence**, not statistical likelihood.

Typical interpretations:
- `0.90-1.00`: Explicit, high-confidence signals
- `0.60-0.89`: Strong heuristic signals
- `0.30-0.59`: Weak or partial signals
- `0.00-0.29`: Default or unknown

Confidence values must be justifiable via reasons.

---

## Rule Behavior

Each inference rule:
1. Consumes normalized input features
2. Evaluates rule-specific signals
3. Produces a structured inference result
4. Does not mutate stored facts
5. Can be safely re-run at any time

Rules are pure functions over input data.

---

## Evolution & Compatibility

Inference logic may evolve over time.

Allowed changes (non-breaking):
- Adding new inference attributes
- Improving confidence calibration
- Adding additional reasons

Breaking changes:
- Changing semantic meaning of an inference value
- Removing inference attributes
- Reinterpreting confidence meaning

Breaking changes must be explicitly versioned.

---

## Enforcement

Inference guarantees are enforced by:
- Determinism tests
- API contract tests
- Schema validation tests

Inference behavior is considered incorrect if it violates this contract, even if tests pass.