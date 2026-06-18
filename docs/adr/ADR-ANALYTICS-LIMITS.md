# ADR-ANALYTICS-LIMITS

Status: Approved

Date: 2026-06-18

## Context

Analytics report generation, statistical validation, and dashboard payloads need
concrete limits before production handoff so performance behavior is measurable
and deterministic.

## Decision

Approved Phase 6 limits on a local developer workstation profile
(Windows, Python 3.14, pandas >=2.0, numpy >=1.20):

- Maximum trades per request: 100,000 closed/open trade records.
- Maximum equity points per request: 250,000 points.
- Maximum benchmark points per request: 250,000 points.
- Maximum portfolio components per request: 250 component results.
- Maximum dashboard returned points per series: 500 points.
- Maximum standard response payload: 3 MB before dashboard truncation.
- Report generation runtime target: 2 seconds for 10,000 trades and 10,000
  equity points.
- Statistical validation runtime target: 5 seconds for 10,000 returns with
  default iteration counts.
- Bootstrap/permutation default iteration count: 1,000.
- Bootstrap/permutation hard iteration cap: 10,000.
- Monte Carlo hard iteration cap: 10,000 simulated paths.
- Distribution fitting sample cap: 100,000 points.
- Memory target: remain below 512 MB incremental resident memory for approved
  benchmark inputs.

Dashboard truncation must be deterministic and must emit truncation metadata:
`truncated`, `original_count`, `returned_count`, `max_points`, and
`downsample_method`.

## Consequences

Performance benchmark tests remain the handoff gate for future larger input
limits. If hardware, Python version, or algorithm choices change, this ADR and
the implementation plan evidence must be updated.
