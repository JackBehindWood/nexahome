"""Everything that reaches the network or reads a release: the checked download (net.py), version comparison
(versions.py) and `nexahome update` (updater.py). Only net.py may import a network module (PK-S2, a test enforces
it). This file imports nothing, so loading one module of the package costs only that module."""
