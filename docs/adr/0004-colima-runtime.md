# 0004. Colima as the laptop container runtime

* **Status:** Confirmed
* **Date:** 2026-10-20

## Context
Only the docker CLI and Compose were installed; no engine ran. The MacBook Air has limited RAM and battery, and containers on macOS always run in a Linux VM.

## Decision
Use Colima (VM created with 2 CPUs, 2 GB RAM, 20 GB disk) behind the existing docker CLI. Compose files stay runtime-agnostic, so any engine can replace it. On Linux hosts Docker Engine runs directly.

## Consequences
Light and open source, no GUI. The VM stops with `colima stop`; its data lives in `~/.colima`. Remove with `colima delete`. No GPU or USB passthrough (true of every macOS runtime).

## Alternatives
Docker Desktop (heaviest, proprietary), OrbStack (light, proprietary).
