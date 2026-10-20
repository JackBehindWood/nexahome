# 0005. Agent configuration stays local

* **Status:** Confirmed
* **Date:** 2026-10-20

## Context
The repository is public. AI-assistant configuration (instructions, permission rules, skills) holds personal working preferences and is not needed to use or contribute to NexaHome.

## Decision
`CLAUDE.md`, `.claude/` and `.vscode/` are gitignored and never committed. Public documents are self-contained: they state the policy (see constraints) and never link to these files.

## Consequences
Public docs read without knowing any assistant exists. The enforcement files must be copied by hand to a new machine. Policy and enforcement can drift; the policy document is the reference.

## Alternatives
Commit sanitised copies (adds a personal-data review and a maintenance burden); commit only the permission rules (couples the repository to one tool).
