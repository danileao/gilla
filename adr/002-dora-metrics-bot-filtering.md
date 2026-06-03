# ADR-002: DORA Metrics — Bot Filtering and Lead Time Display

**Status:** Accepted  
**Date:** 2026-06-02  
**Author:** DevEx Platform Team

## Context

DORA metrics require querying GitHub API for deployment, PR, and workflow run data. Two specific challenges:

1. Bot PRs (Dependabot, Renovate) skew lead time metrics — they auto-merge within seconds
2. Lead times can range from milliseconds to weeks — the display must be human-readable

## Decision

### Bot filtering

- Filter PRs where `user.type == "Bot"` before calculating lead time
- Track and display how many bot PRs were excluded
- Only affects lead time — deployment and failure metrics use raw data

### Display logic

- Show seconds (`.Xs`), minutes (`Xm`), or hours (`X.Xh`) depending on magnitude
- Threshold: < 1s → `.Xs`, < 1m → `X.Xs`, < 1h → `Xm`, else `X.Xh`
- Precisely store the raw median value (no rounding) and format only at display time
- When lead times are very small (< 3.6s), append a counter showing how many PRs had near-zero lead

### Mock mode

- `--mock` flag for demo and testing without a real GitHub token
- Uses seeded random values (`hash(owner/repo/days)`) for reproducible output

## Consequences

- Bot PRs won't artificially deflate lead time metrics
- User can verify how many PRs were excluded
- Display adapts to any lead time magnitude
- Raw values are preserved in `dora-metrics.json` for external tools
- Mock mode enables CI testing and presentations without API access
