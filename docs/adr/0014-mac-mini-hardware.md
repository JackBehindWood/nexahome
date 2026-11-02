# 0014. Mac mini hardware choice

* **Status:** Proposed (drafted after the purchase; confirmed or corrected in P4 B2, inside the return window)
* **Date:** 2026-11-02

## Context
The first planned hardware step is a Mac mini ([register](../project.md#decision-register)). Use is at the desk (monitor, keyboard, Wi-Fi), mostly idle, with nothing on it that must stay up. The goal is a workstation for development and local AI. RAM and storage are soldered, so a wrong size cannot be fixed later. Prices, discounts and lead times are not recorded here: they change, and the budget is the owner's.

Requirements and how each is verified: H1 at most three options, each priced from a live source before buying (review; the figures stay local); H2 a named model answers a prompt natively and memory headroom is measured with the model loaded and the container runtime up (B2, figures in the session log); H3 a go or no-go inside the return window (B2, decision by day 12 of 14); H4 nothing personal or financial in tracked files (`make check`).

## Decision
Apple Mac mini, M6, **32 GB memory, 512 GB internal storage**, bought new, plus a small **external SSD** (about 1 TB) for a copy of the backup repository, spare models and scratch space. The external disk is beside the mini, so it is not off-site and not 3-2-1; its file system is tested in B3 before it counts.

| | A: M6, 24 GB / 512 GB | **B: M6, 32 GB / 512 GB** | C: M5 Pro, 24 GB / 512 GB (reference) |
| :-- | :-- | :-- | :-- |
| Cost tier | lowest | middle | highest |
| Model size | up to 14B comfortable; 27 to 30B tight | 30B class (about 19 GB at 4-bit) with a capped context | same memory as A; higher bandwidth means faster decoding, not a bigger model |
| Fit | a 14B goal | the stated goal, local AI to replace paid usage, at a price in reach | only if the education price is clearly lower and speed matters more than model size |

Fallback: M6 with 16 GB only if the small-model test had shown a small model suffices; it cannot run the 30B class. There is no wait for a newer generation: this one is current.

Sizing rule (re-measured in B2): weights (parameters times bits per weight, divided by 8) plus KV cache for the chosen context, plus 4 to 6 GB for macOS, plus 2 to 4 GB for the Colima VM, plus 10% headroom. On 32 GB with a 19 GB model this leaves little for the cache, so the context is capped. 512 GB covers the system, tens of GB of models, the Colima disk and the backup repository; 256 GB would be tight.

| On the mini | Not on the mini |
| :-- | :-- |
| native model server, light stacks (`hello`, `actual`), development, Claude Code, backups and a copy of the repository | identity provider, health monitor, anything needed while the mini is off or asleep ([architecture](../architecture.md)) |

Return-window rule: unbox and run B1 and B2 within 5 days of receipt; send the return notice by day 12 of the 14 if the model test fails.

## Consequences
Easier: one machine covers development and a 30B-class local model within budget; the same Compose files run on it ([ADR 0004](0004-colima-runtime.md)). Harder: memory and disk are fixed for the life of the machine; the model and Colima VM compete for 32 GB; a local model is weaker than a cloud agent at tool use, so the cloud agent stays for coding and the local one is a measured complement (B5). Saving money is real only if a subscription is cancelled; that is the owner's call, not an exit criterion.

Evolution per hop is in [architecture](../architecture.md#migration-paths). When a NAS exists the backup copy moves there and the external disk becomes spare capacity.

## Alternatives
M5 Pro (reference, see table); 16 GB models (fallback only); a used or refurbished machine (not wanted: new only); a Linux box with a GPU (more power, noise and cost, no Apple silicon memory sharing); waiting for the next generation (this one is current; costs were rising, not shown to be cheaper).

## Verification and status
The owner dropped the planned small-model laptop test (strategy: local AI now, hybrid with a cloud agent later), so the choice rests on the sizing rule, not on a measurement; B2 is the first measurement. Live prices were checked by the owner and are kept local. **Not verified:** M6 idle and load power, tokens per second for the chosen model, whether the 30B class fits with Colima running, the macOS version the mini ships with, the external disk's file system with the backup job (B3). The choice closes "local AI model size" and "storage, budget and power" in the register only on the owner's explicit yes.
