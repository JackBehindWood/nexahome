"""macOS: Docker CLI from Homebrew, containers in a Colima VM (ADR 0004)."""

from nexahome.platform.host import Host

NAME = "macos"
REFUSAL = None
MOUNTS_HOME_ONLY = True


def docker_install_fix(host: Host) -> str:
    return "brew install colima docker docker-compose"


def compose_install_fix(host: Host) -> str:
    return (
        "brew install docker-compose && mkdir -p ~/.docker/cli-plugins && "
        'ln -sfn "$(brew --prefix)/opt/docker-compose/bin/docker-compose" ~/.docker/cli-plugins/docker-compose'
    )


def engine_start_fix(host: Host) -> str:
    return "colima start --cpu 2 --memory 2 --disk 20"


def engine_restart_fix(host: Host) -> str:
    return "colima restart"
