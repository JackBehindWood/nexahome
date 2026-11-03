# Stack name

One sentence: what this stack does and why it exists.

```sh
make up STACK=<name>      # start and wait until healthy
make down STACK=<name>
```

| Item | Value |
| :--- | :--- |
| RAM (measured) | |
| Disk (measured) | |
| Must run 24/7? | yes / no |
| Backed up | volumes labelled `nexahome.backup: "true"`; list them |
| Verify after a restore | one concrete check, for example a known item in the app |

Variables are listed in `.env.example`. Dummy data only in this repository.
