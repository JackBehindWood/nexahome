"""Every tunable number and name the package shares, in one place (a limit, a timeout, a mode, a setting name).

Literals only: no import, no logic, so importing this file costs one small module and nothing it depends on. A
module imports the values it uses, inside the function that uses them where it can; `nexahome --version` never loads
this file. A value used by one domain only and part of its contract (the Compose policy, `docker.EDGE_NETWORK`)
stays with that domain. tests/test_defaults.py enforces the shape.
"""

# Time limits, in seconds
DOCKER_TIMEOUT = 15  # `docker version`, `docker info`, `compose ps`: a stuck VM must not hang the command
LOGS_TIMEOUT = 60  # `compose logs --tail N` for one stack (not used with --follow, which runs until Ctrl-C)
LOG_TAIL = 100  # lines per service when --tail is not given
PROBE_TIMEOUT = 10  # the same questions asked by `doctor`, which must stay quick
COMPOSE_CONFIG_TIMEOUT = 60  # per stack: `config` reads and interpolates every file
FEED_TIMEOUT = 15  # the release feed and its checksum list
WHEEL_TIMEOUT = 120  # the wheel download
INSTALL_TIMEOUT = 300  # `uv tool install`

# Size limits, in bytes, and worker counts
FEED_MAX_BYTES = 1_000_000
WHEEL_MAX_BYTES = 50_000_000
DOWNLOAD_CHUNK_BYTES = 65536
STACK_FILE_MAX_BYTES = 1024 * 1024  # a stack file is configuration; anything bigger is not ours to copy
CONFIG_MAX_BYTES = 64 * 1024  # nexahome.toml
MAX_WORKERS = 8  # independent subprocess calls run side by side, at most this many

# Thresholds
LOW_DISK_BYTES = 5 * 1024**3
BACKUP_RECENT_SECONDS = 7 * 24 * 3600
SECRET_LENGTH = 48  # characters of a generated secret

# File modes: package files are not secret and a container user must read them whatever the umask
PUBLIC_FILE_MODE = 0o644
PUBLIC_DIR_MODE = 0o755
PRIVATE_FILE_MODE = 0o600

# Settings read from the environment
ENV_HOME = "NEXAHOME_HOME"
ENV_BACKUP_DIR = "NEXAHOME_BACKUP_DIR"
ENV_UPDATE_URL = "NEXAHOME_UPDATE_URL"
ENV_DEBUG = "NEXAHOME_DEBUG"

# Stacks
DEFAULT_STACKS = ("hello",)  # a fresh instance runs the demo; more are added with `nexahome config set stacks`
CORE_STACKS = ("edge", "identity")  # started first, as the Makefile does
NON_SERVICE_STACKS = ("_template", "backup")  # the template, and the one-shot backup tool
DEMO_PORT = 8080

# Output contracts: four separate schemas that happen to be 1 today. A change to one is not a change to the others.
INSTANCE_SCHEMA = 1  # nexahome.toml and the manifest; a newer one is refused, never guessed
REPORT_SCHEMA = 1  # `doctor --json`
STACKS_JSON_SCHEMA = 1  # `stacks --json`
UPDATE_JSON_SCHEMA = 1  # `update --available --json`
