"""Everything NexaHome knows about the Docker CLI lives in this package, so a change in how it is called is made once.

- engine.py:  the CLI and the engine (`docker --version`, `docker info`)
- compose.py: Compose (`docker compose` version, ps, config, the `-f` and `--env-file` arguments)
- probes.py:  the three `doctor` checks that ask those questions

What differs between operating systems (how to install or start Docker) stays in `nexahome.platform`; what the
Compose files must look like is the policy in `nexahome.policy.compose`. This file imports nothing, so loading one
module of the package costs only that module.
"""

EDGE_NETWORK = "nexahome-edge"  # the one network shared by the stacks; the Makefile still holds its own copy until PK7
