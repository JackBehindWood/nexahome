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


def test_only_platform_py_knows_the_operating_system() -> None:
    offenders = [p.name for p in SOURCES if p.name != "platform.py" and OS_SPECIFIC.search(p.read_text())]
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
