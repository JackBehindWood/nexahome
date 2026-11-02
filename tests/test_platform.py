import sys
import types

import pytest

from nexahome import platform
from nexahome.errors import ExitCode, NexaHomeError

from conftest import MakeHost


def test_current_describes_this_machine() -> None:
    host = platform.current()
    assert host.system in ("macos", "linux", "windows")
    assert host.python == tuple(sys.version_info[:3])
    assert host.home.is_absolute()


@pytest.mark.parametrize(
    ("sys_platform", "machine", "system", "normalised"),
    [
        ("darwin", "arm64", "macos", "arm64"),
        ("linux", "aarch64", "linux", "arm64"),
        ("linux", "x86_64", "linux", "amd64"),
        ("win32", "AMD64", "windows", "amd64"),
        ("freebsd14", "riscv64", "linux", "riscv64"),  # best effort: anything else counts as Linux
    ],
)
def test_current_normalises_system_and_machine(
    monkeypatch: pytest.MonkeyPatch, sys_platform: str, machine: str, system: str, normalised: str
) -> None:
    monkeypatch.setattr(platform, "sys", types.SimpleNamespace(platform=sys_platform, version_info=sys.version_info))
    monkeypatch.setattr(platform.stdlib_platform, "machine", lambda: machine)
    host = platform.current()
    assert (host.system, host.machine) == (system, normalised)


@pytest.mark.parametrize(
    ("text", "debian_like"),
    [
        ('ID=ubuntu\nID_LIKE=debian\n', True),
        ('ID="debian"\n', True),
        ('ID=linuxmint\nID_LIKE="ubuntu debian"\n', True),
        ("ID=fedora\nID_LIKE=rhel\n", False),
        ("", False),
    ],
)
def test_parse_os_release(text: str, debian_like: bool) -> None:
    assert platform.parse_os_release(text) is debian_like


def test_native_windows_is_refused_with_wsl2(make_host: MakeHost) -> None:
    with pytest.raises(NexaHomeError) as raised:
        platform.require_supported(make_host(system="windows"))
    assert "WSL2" in raised.value.message
    assert raised.value.fix == "wsl --install"
    assert raised.value.exit_code == ExitCode.NOT_READY


@pytest.mark.parametrize("system", ["macos", "linux"])
def test_macos_and_linux_are_accepted(make_host: MakeHost, system: str) -> None:
    platform.require_supported(make_host(system=system))


def test_describe(make_host: MakeHost) -> None:
    assert platform.describe(make_host(system="macos", machine="arm64")) == "macOS arm64"
    assert platform.describe(make_host(system="linux", machine="amd64")) == "Linux amd64"


def test_fix_strings_per_system(make_host: MakeHost) -> None:
    mac, debian, other = make_host(system="macos"), make_host(debian_like=True), make_host()
    assert platform.engine_start_fix(mac).startswith("colima start")
    assert platform.engine_start_fix(debian) == "sudo systemctl start docker"
    assert platform.docker_install_fix(mac).startswith("brew install")
    assert platform.docker_install_fix(debian).startswith("sudo apt-get install")
    assert platform.docker_install_fix(other).startswith("https://docs.docker.com/")  # the documented exception
    assert platform.compose_install_fix(mac).startswith("brew install docker-compose")
    assert platform.colima_mount_applies(mac) and not platform.colima_mount_applies(other)
    assert platform.is_supported_machine(mac.__class__("linux", "arm64", (3, 13, 0), mac.home))
    assert not platform.is_supported_machine(make_host(machine="riscv64"))
