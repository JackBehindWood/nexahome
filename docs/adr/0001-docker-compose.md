# 0001. Docker Compose as the container orchestrator

* **Status:** Confirmed
* **Date:** 2026-10-20

## Context
NexaHome starts on a single laptop and later grows to a few hosts. It needs a reproducible, readable way to run containers.

## Decision
Use Docker Compose for all container workloads. One stack per directory under `stacks/`.

## Consequences
Simple, portable between macOS and Linux, easy to read. No cluster scheduling or automatic failover.

## Alternatives
Kubernetes or k3s (too complex for the scale), custom scripts (reinvents Compose).
