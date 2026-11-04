# Security policy

## Reporting a vulnerability

Do not open a public issue with details. Use "Report a vulnerability" in this repository's Security tab.

## Scope

The code, configuration and documents in this repository, including the `nexahome` command and how `nexahome update` downloads and verifies a release. Your own deployment, hardware and network are your responsibility.

## Supported versions

The latest release; until the first release exists (none yet), `main`. Fixes land there, with no backports.

## Response

Best effort, without a promised response time. This is a solo hobby project.

## If a secret was committed

Treat it as compromised: rotate it first, then report it. The full list of what must never be committed is in [constraints](docs/constraints.md#security-rules).
