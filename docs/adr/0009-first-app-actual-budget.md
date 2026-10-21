# 0009. First application: Actual Budget

* **Status:** Proposed
* **Date:** 2026-10-21

## Context
The backup and restore drill (P2) needs one real stateful stack: a single container, no database server, arm64, a permissive open-source licence, non-root capable and useful long term. Expense tracking is a planned application (P8).

## Decision
Use Actual Budget as `stacks/actual`, image `actualbudget/actual-server:26.10.0-alpine`. Checked on 2026-10-21: MIT licence; arm64 image published; SQLite; port 5006; data in `/data`. Run as uid 1001 with a read-only root and a tmpfs `/tmp`: the image runs as root and has no health check by default, so the stack overrides both. Proven here: healthy, uid 1001, writes `/data`, about 130 MiB RAM idle.

Owner direction (2026-10-21): Actual is the drill subject only, not the long-term expense tracker. The owner plans to build an own expense app later (P8, its own ADR). Until then Actual stays, with dummy data, and can be removed once another stateful stack exists.

## Consequences
The drill covers a real SQLite file. The tag is pinned and updated by Dependabot. Not verified: outbound network calls (update or version checks), behaviour across upgrades, and that real financial data is safe before the restore drill passes (dummy data only until then).

## Alternatives
Other expense trackers were not evaluated; Actual was the one candidate checked against the criteria. A throwaway placeholder app was rejected because nothing from it carries forward.
