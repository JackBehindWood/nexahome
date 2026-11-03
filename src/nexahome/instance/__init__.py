"""An instance is a folder that holds the stacks and the state of one NexaHome install: a git clone, or a folder made
by `nexahome init`.

- home.py:     which folder is the instance (the resolution order, shared by every command)
- bundle.py:   the stacks that ship inside the package
- create.py:   what `nexahome init` does
- config.py:   `nexahome.toml`, read strictly and written atomically
- manifest.py: the hashes of the package-owned files, for the future `upgrade`

This file imports nothing, so loading one module of the package costs only that module.
"""

CONFIG_NAME = "nexahome.toml"  # at the top of an instance made by `nexahome init`; a clone has none
SCHEMA = 1  # the layout of nexahome.toml and the manifest; a newer one is refused, never guessed
