# Add a stack

**Audience:** developers and contributors. **Admin rights needed:** no.

```sh
cp -R stacks/_template stacks/<name>   # then edit compose.yaml, .env.example, README.md
make check                             # label, project name and Compose policy
make up STACK=<name>
make ps STACK=<name>
make down STACK=<name>
```

Checklist before the pull request:

1. `name:` is `nexahome-<name>`; the image has an exact tag and supports arm64.
2. Every named volume has `nexahome.backup: "true"` or `"false"`.
3. Ports bind to `127.0.0.1` with the host port from a variable that has a default; every variable is in `.env.example` (placeholders only; `CHANGE_ME` makes `make up` stop).
4. The README records measured RAM and disk, whether the stack must run 24/7, what is backed up and how to verify a restore.
5. Add a `docker-compose` entry for `/stacks/<name>` to `.github/dependabot.yml`.
6. A significant choice (for example the application itself) gets an ADR.

Rules: [Compose policy](../constraints.md#compose-policy). Contract: [ADR 0007](../adr/0007-stack-contract.md).
