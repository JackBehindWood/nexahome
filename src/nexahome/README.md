# nexahome

The code behind the `nexahome` command: checks for your machine and your stacks, and the commands that make a folder of stacks you can run. Standard library only. It starts no container itself; stack commands call `docker compose` on the host.

Where things are: the module map is in [docs/codebase.md](../../docs/codebase.md#layout) (one place, so it stays true). Start there for:

- how to add a command or a `doctor` check ([Extending it](../../docs/codebase.md#extending-it));
- what already exists before you write a helper ([Reuse before you write](../../docs/codebase.md#reuse-before-you-write));
- how to keep start-up fast ([Keeping the command fast](../../docs/codebase.md#keeping-the-command-fast));
- shell or Python for new code ([Script or package?](../../docs/codebase.md#script-or-package)).

Tests are in [`tests/`](../../tests), mirroring these folders; run `make test`. The reasons for the design: [ADR 0018](../../docs/adr/0018-code-package-and-language-strategy.md).
