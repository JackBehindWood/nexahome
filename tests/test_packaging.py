"""Rules about the package itself, checked mechanically."""

import ast
import importlib.metadata
import re
from pathlib import Path

import nexahome

PACKAGE = Path(nexahome.__file__).parent
SOURCES = sorted(PACKAGE.rglob("*.py"))
OS_SPECIFIC = re.compile(r"sys\.platform|^\s*(?:import|from)\s+platform\b|os\.uname|os\.name\b|\buname\b|os-release", re.M)
POSIX_ONLY_IMPORTS = re.compile(r"^\s*(?:import|from)\s+(?:fcntl|pwd|grp|termios|resource)\b", re.M)


def test_no_runtime_dependencies() -> None:
    assert importlib.metadata.requires("nexahome") is None  # PK-C1


def test_only_the_platform_package_knows_the_operating_system() -> None:
    offenders = [str(p.relative_to(PACKAGE)) for p in SOURCES if "platform" not in p.relative_to(PACKAGE).parts[:1] and p.name != "platform.py" and OS_SPECIFIC.search(p.read_text())]
    assert offenders == []  # PK-P3


def test_nothing_imports_posix_only_modules() -> None:
    assert [p.name for p in SOURCES if POSIX_ONLY_IMPORTS.search(p.read_text())] == []


def test_no_shell_is_ever_used() -> None:
    assert [p.name for p in SOURCES if "shell=True" in p.read_text() or "os.system" in p.read_text()] == []


def test_every_function_is_fully_annotated() -> None:  # PK-C4 without a type checker
    missing: list[str] = []
    for path in SOURCES:
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            args = node.args
            every = [*args.posonlyargs, *args.args, *args.kwonlyargs, *filter(None, [args.vararg, args.kwarg])]
            unannotated = [a.arg for a in every if a.annotation is None and a.arg not in ("self", "cls")]
            if unannotated or node.returns is None:
                missing.append(f"{path.name}:{node.lineno} {node.name}")
    assert missing == []


def test_the_package_is_marked_typed() -> None:
    assert (PACKAGE / "py.typed").is_file()


NETWORK = re.compile(r"^\s*(?:import|from)\s+(?:urllib|http|socket|ssl|ftplib|smtplib|requests)\b", re.M)


def test_only_net_py_touches_the_network() -> None:
    assert [p.name for p in SOURCES if p.name != "net.py" and NETWORK.search(p.read_text())] == []  # PK-S2


# "Pay for what you use" (ADR 0021): heavy standard-library modules are imported inside the function that needs them.
HEAVY_AT_TOP = {
    "json", "subprocess", "hashlib", "hmac", "tempfile", "secrets", "random", "shutil", "shlex", "urllib", "ssl", "http",
    "concurrent", "dataclasses", "inspect", "platform", "socket", "logging", "pkgutil", "zipfile", "email", "argparse",
}
# (file, module) pairs that must load whenever that file is loaded, because the file is only loaded by a command that needs it
ALLOWED_AT_TOP = {
    ("runner.py", "subprocess"),  # every command that gets as far as running a program
    ("policy/compose.py", "json"),  # only loaded by `check`
    ("updater.py", "json"),  # only loaded by `update`
    ("commands/_base.py", "argparse"),  # types only; never imported at run time
}


def test_heavy_modules_are_imported_inside_functions() -> None:
    found: list[str] = []
    for path in SOURCES:
        relative = path.relative_to(PACKAGE).as_posix()
        for node in ast.parse(path.read_text()).body:  # module level only
            if isinstance(node, ast.If) and getattr(node.test, "id", "") == "TYPE_CHECKING":
                continue
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
            found += [f"{relative}: {n}" for n in names if n.split(".")[0] in HEAVY_AT_TOP and (relative, n.split(".")[0]) not in ALLOWED_AT_TOP]
    assert found == []


def test_docker_knowledge_lives_in_the_docker_package() -> None:
    """PK6-16: the program name and the shared network are named once, in nexahome/docker/; elsewhere they are imported."""
    found = []
    for path in SOURCES:
        relative = path.relative_to(PACKAGE).as_posix()
        if relative.startswith("docker/"):
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Constant) and node.value in ("docker", "nexahome-edge"):
                found.append(f"{relative}:{node.lineno} {node.value!r}")
    assert found == []
