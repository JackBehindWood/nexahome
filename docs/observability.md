# NexaHome: Observability & Operations

## 1. Management & Observability Layers

The platform aims to build toward a unified management view separating the following domains:

1. **Service Discovery & Portal:** Navigation and links to active web applications and services.
2. **Health & Availability:** Uptime monitoring, probe status, and alert notifications.
3. **Telemetry & Logs:** Aggregated metrics, resource usage (CPU/RAM/Disk), and log collection.
4. **Deployment & Config Status:** Track active container versions, Git commit state, and drift.
5. **Backups & Recovery:** Job execution history, backup integrity, and restoration readiness.
6. **Asset Inventory:** Hardware inventory, assigned local IPs, and network topology map.

*The asset inventory contains hostnames and IPs, so it must stay private: keep it in a gitignored `inventory.local.md` or outside the repository, and publish only a template.*

---

## 2. Observability Strategy

* Start with lightweight, existing open-source tools before building custom solutions.
* A dedicated **NexaHome Dashboard** may be created in later phases once system interfaces mature.
* **Decoupling:** Critical services (DNS, storage, core AI) must never depend on the monitoring/dashboard suite to function.

## 3. Phase 0 (laptop only)

No monitoring suite. Use container health checks and `docker compose ps` to see service state. Choose a portal or uptime tool only after one real service exists.
