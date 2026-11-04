# stacks

One folder per service, each a unit you can start and stop alone: `compose.yaml`, `.env.example` and a README. The rules every stack follows (non-root, read-only, pinned image tag, ports on 127.0.0.1, labelled volumes) are the [Compose policy](../docs/constraints.md#compose-policy) and [ADR 0007](../docs/adr/0007-stack-contract.md); `nexahome check` enforces them.

| You want to | Read |
| :-- | :-- |
| run a stack | the root [README](../README.md); `nexahome stacks` lists what exists and what this host runs |
| make your own stack, from the installed package | [Make your own stack](../docs/runbooks/own-stack.md) (`nexahome stacks new NAME`) |
| add a stack to the project, from a clone or a fork | [Add a stack](../docs/runbooks/add-a-stack.md); start from [`_template/`](_template/README.md) |
| know what a stack's README must hold | [`_template/README.md`](_template/README.md) |

In an installed instance the stacks that came with the package belong to it: do not edit them; your own stacks sit beside them in the same folder. Each stack's `.env` is local and never committed. Backups, ports and idle RAM are recorded in each stack's own README.
