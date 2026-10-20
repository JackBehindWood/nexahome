# NexaHome: Architecture & Infrastructure

## 1. Logical Architecture Layers

NexaHome is structured into six logical layers. Cross-cutting concerns (monitoring, configuration management, documentation, security, and backup policies) apply across all layers.

| Layer | Domain | Description / Scope |
| :--- | :--- | :--- |
| **1** | **Physical Infrastructure** | Computers, storage, power (UPS), cooling, physical networking. |
| **2** | **Network & Security** | Routing, DNS, VPN, firewalls, and network access controls. |
| **3** | **Compute Platform** | Hosts, Docker, and virtualization environments. |
| **4** | **Data & Storage** | Databases, file storage, persistent volumes, and backup destinations. |
| **5** | **Service Platform** | APIs, service containers, messaging, auth, and shared services. |
| **6** | **Applications** | AI tools, finance tools, media, home automation, and user dashboards. |

*Note: These are logical boundaries, not separate physical machines. Multiple components may share hardware when failure implications are understood.*

**Terms.** *Layer*: one row above. *Host*: a physical machine running workloads. *Stack*: one deployable unit (a directory under `stacks/` with its Compose file, example env file, and README).

---

## 2. Hosts

| Host | Availability | Role |
| :--- | :--- | :--- |
| **MacBook Air M3** | Available now | Development and test only. Portable, sleeps, nothing depends on it being up. |
| **Mac mini** | Planned | Primary workstation, development, and local AI (run natively on the host). Not relied on for always-on services. |
| **NAS / dedicated server** | Planned | Persistent storage, backups, media, and 24/7 background services. |
| **Network infrastructure** | Planned | Upgraded switches, secure remote access, segmentation. |
| **UPS** | Planned | Power resilience for server and NAS. |

### Hardware Assumptions & Constraints
* **Do not assume planned hardware is available today.**
* The Mac mini serves as a personal workstation; it may sleep, so the architecture **must not** depend on it being available at all times. Always-on services belong on the NAS or a dedicated server.
* Containers on macOS run inside a Linux VM: they cannot use the GPU or pass through USB devices. Local AI therefore runs natively on the host, not in containers.

### Remote access
SSH from the MacBook Air to the Mac mini is required (goal confirmed, method open; see the roadmap). Access is key-only and never exposed publicly. Details go into a runbook once the hardware exists.

---

## 3. Intended Platform Capabilities

Capabilities are implemented incrementally. "Now" means possible on the laptop alone.

| Capability | Scope | Now |
| :--- | :--- | :--- |
| **DevOps & Code:** development environments, Git workflows, automated testing | Core | Yes |
| **Management Interface:** central portal for system status and personal app navigation | Core | Later, once a service exists |
| **AI & Automation:** local LLMs, coding agents, personal AI assistant tools | Local AI runs natively | Limited; fuller on Mac mini |
| **Personal Finance:** expense tracking, portfolio monitoring | Applications | Possible, low priority |
| **Data & Storage:** central file storage, photos, media streaming, automated backups | Needs NAS | Restore drill on a local volume only |
| **Smart Home:** Home Assistant, MQTT, ESP32 microcontrollers | Needs USB/network access | Needs Linux host |
| **Core Network:** internal DNS, ad-blocking, VPN, secure remote access | Needs always-on host and network gear | No |

## 4. Data placement

Persistent data lives outside the code tree. Compose reads a data root from the `NEXAHOME_DATA_DIR` environment variable (laptop default: `./data`, gitignored). Use named volumes for database-style data on macOS and bind mounts for configuration only.
