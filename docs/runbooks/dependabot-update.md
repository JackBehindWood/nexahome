# Update a stack from a Dependabot pull request

Version 0.1 · Last reviewed 2026-11-04

**Audience:** anyone running NexaHome who got a Dependabot pull request that bumps an image tag in a stack. **Admin rights needed:** no. Needs the container runtime running, a working backup ([restore runbook](restore.md)) and about 10 minutes per stack. Drilled on the laptop with Gatus (v5.37.0 to v5.38.0) and Pocket ID (v2.18.0 to v2.19.2); not drilled on Linux or on the Mac mini.

The pull request only changes a tag. Merging it changes nothing that runs: you start the new version yourself, after a backup, and you can undo it. Replace `<stack>` and `<old-tag>` below.

1. **Read the release notes first.** The pull request body quotes them. Look for: a database or settings migration, removed or renamed environment variables, new defaults that change who may sign in or what leaves the machine. Check the release date upstream: the "cooldown could not be applied" warning on a pull request means Dependabot did not know it. Hold the pull request (see the end) if a note says a migration is one-way.
2. **Back up with the stack stopped** (a running database changes while it is copied):

   ```sh
   make down STACK=<stack>
   make backup STACK=<stack>
   make verify STACK=<stack>      # expect: verify <stack>/data: equal
   ```

   A stack whose volume is labelled `nexahome.backup: "false"` (Gatus history) is not saved; its data is disposable, so skip to step 3.
3. **Bump the tag.** Edit the tag in `stacks/<stack>/compose.yaml` (for Gatus, the `FROM` line in `stacks/gatus/Dockerfile`) to the pull request's version, then `make check`. Or check out the pull request branch.
4. **Start it and test it:**

   ```sh
   make up STACK=<stack>          # a stack with a Dockerfile is rebuilt
   make smoke                     # expect: smoke: all checks passed
   docker logs nexahome-<stack>-<service>-1 2>&1 | grep -i "migrat\|ERR\|WRN"
   docker stats --no-stream
   ```

   Open the stack's page through the edge. Compare memory with the figure in the stack's README; a limit hit shows as a restart (`docker inspect -f '{{.RestartCount}}' <container>`; smoke fails on a restart).
5. **Merge the pull request** only when steps 2 to 4 pass and you have used the app once.

## Roll back

- **No migration in the log** (Gatus drill: history kept in both directions): put the old tag back, `make up STACK=<stack>`, `make smoke`.
- **A migration ran or the old version will not start** (Pocket ID drill: v2.19.2 ran `08-management.sql`; v2.18.0 then refused the data with "downgrades are not allowed" and restarted in a loop): the data cannot go back by changing the tag. Restore the backup from step 2:

  ```sh
  make down STACK=<stack>
  docker volume rm nexahome-<stack>_data      # restore never overwrites
  make restore STACK=<stack>
  # put <old-tag> back, then:
  make up STACK=<stack> && make smoke
  ```

  Anything the app wrote after the backup is lost. Then close the pull request or comment on it; Dependabot will not propose the same version again.

## Hold a pull request

Keep it open and note why when: the release notes describe a one-way migration and you have no restore-tested backup; smoke fails or a container restarts; memory exceeds the stack's limit; the app behaves differently (sign-in, redirects, defaults) and nobody has decided to accept that; a check other than the known abandoned `platforms` job is red; or the tag is a major version (the Pocket ID notes announce v3 and say to pin a major, never `latest`).

Rehearse on a separate engine first when the data matters: `colima start drill` uses its own volumes and networks, so a copy of the repository there cannot touch your running stacks (set `DOCKER_CONTEXT=colima-drill`; keep the copy under your home directory, because the VM does not mount `/tmp`).

Changelog: 0.1 (2026-11-04): first version, from the Gatus v5.38.0 and Pocket ID v2.19.2 drills.
