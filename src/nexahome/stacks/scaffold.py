"""Make and remove a stack of your own (Proposed, Goal 3).

`new_stack` copies the bundled `_template` into `stacks/<name>`, renames it, and (in an instance) adds the name to
`nexahome.toml`. `remove_stack` deletes a stack the user made, after listing what goes; it never deletes Docker
volumes and never touches a package stack. Nothing here runs a process except the one `docker compose ps` that
`remove_stack` needs to know the stack is stopped.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from nexahome import files
from nexahome.defaults import PUBLIC_FILE_MODE
from nexahome.errors import NexaHomeError
from nexahome.instance import home

if TYPE_CHECKING:
    from nexahome.context import Context

TEMPLATE_FILES = ("compose.yaml", ".env.example", "README.md")
FIRST_PORT = 8081  # the template's own default; later stacks take the next free one


class NewStack(NamedTuple):
    folder: Path
    port: int
    enabled: bool  # added to nexahome.toml (an instance); a clone has no list


def _check_name(name: str, verb: str) -> None:
    from nexahome.instance.config import STACK_NAME

    if not STACK_NAME.fullmatch(name):
        suggestion = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-_") or "mine"
        raise NexaHomeError(
            f"{name!r} is not a stack name (lower-case letters, digits, - and _; it starts with a letter or digit)",
            f"nexahome stacks new {suggestion}" if verb == "new" else "nexahome stacks",
        )


def _free_port(instance: Path) -> int:
    """The smallest port from 8081 that no other stack uses as a `${VAR:-port}` default (the template does not count)
    and that nothing on this host is listening on."""
    from nexahome.release import net

    used: set[int] = set()
    for compose in home.stacks_dir(instance).glob("*/compose.yaml"):
        if compose.parent.name == "_template":
            continue
        try:
            used |= {int(port) for port in re.findall(r":-(\d{2,5})\}", compose.read_text())}
        except (OSError, UnicodeDecodeError):
            continue
    port = FIRST_PORT
    while port in used or net.port_is_busy(port):
        port += 1
    return port


def _render(filename: str, text: str, name: str, port: int, has_make: bool) -> str:
    """The template file with this stack's name, port variable and commands. Without a Makefile (an instance) the
    commands are the ones a runner can type."""
    from nexahome.docker import compose

    variable = name.replace("-", "_").upper()
    if variable[0].isdigit():
        variable = f"S_{variable}"  # a shell variable cannot start with a digit
    text = text.replace("TEMPLATE_PORT", f"{variable}_PORT").replace("nexahome-_template", f"nexahome-{name}")
    text = text.replace(f":-{FIRST_PORT}}}", f":-{port}}}").replace(f"{variable}_PORT={FIRST_PORT}", f"{variable}_PORT={port}")
    if filename == "compose.yaml":
        keep = [line for line in text.splitlines() if not line.startswith(("# Copy this directory", "# The project name must be"))]
        return f"# {name}: replace the image and command with your service, then run: nexahome check\n" + "\n".join(keep) + "\n"
    if filename == ".env.example":
        keep = [line for line in text.splitlines() if "Example of a value you must replace" not in line and not line.startswith("TEMPLATE_SECRET=")]
        text = "\n".join(keep).rstrip() + "\n"
        return text if has_make else text.replace("`make up` creates", "`nexahome env` creates")
    text = text.replace("# Stack name", f"# {name}")
    if not has_make:
        text = text.replace("make up STACK=<name>     ", f"{compose.up_command(name)}").replace("make down STACK=<name>", compose.down_command(name))
    return text.replace("<name>", name)


def new_stack(ctx: Context, instance: Path, name: str) -> NewStack:
    """Create stacks/<name> from the bundled template. Never overwrites; if anything fails, what this call made is removed."""
    from nexahome.instance import REINSTALL, bundle, config
    from nexahome.stacks import ownership

    _check_name(name, "new")
    if name in ownership.package_owned(instance):
        raise NexaHomeError(f"{name} is part of NexaHome; choose a name of your own", f"nexahome stacks new {name}-2")
    folder = home.stack_dir(instance, name)
    if folder.exists() or folder.is_symlink():
        raise NexaHomeError(f"stacks/{name} already exists; new never overwrites", "nexahome stacks")
    source = bundle.location()
    if source is None or not all((source / "_template" / file).is_file() for file in TEMPLATE_FILES):
        raise NexaHomeError("this install carries no stack template", REINSTALL)
    has_make = home.has_makefile(instance)
    port = _free_port(instance)
    texts = {file: _render(file, (source / "_template" / file).read_text(), name, port, has_make) for file in TEMPLATE_FILES}
    listed = home.has_settings(instance)
    created: list[Path] = []
    with files.Rollback(created, "stacks new", f"nexahome stacks new {name}"):
        files.make_directory(folder, created)
        for file, text in texts.items():
            files.create_exclusive(folder / file, text.encode(), PUBLIC_FILE_MODE, created)
        if listed:
            settings = config.read(instance)
            config.write(instance, [*(settings.stacks if settings else ()), name])
    return NewStack(folder, port, listed)


def remove_stack(ctx: Context, instance: Path, name: str, assume_yes: bool) -> bool:
    """Delete stacks/<name> and drop it from nexahome.toml after showing what goes. True when removed, False when the
    user said no. Refuses a package stack, a running stack, a folder with a link in it, and an empty list."""
    import shutil

    from nexahome.docker import compose
    from nexahome.instance import config
    from nexahome.stacks import ownership

    _check_name(name, "remove")
    folder = home.stack_dir(instance, name)
    shown = ctx.display(folder)
    if not home.has_settings(instance):
        raise NexaHomeError(f"{shown}: remove works in a folder made by nexahome init; this one is a clone", f"rm -r {shown}")
    if name in ownership.package_owned(instance):
        raise NexaHomeError(f"{name} is part of NexaHome and is not removed here; to stop using it, change the list", "nexahome config get stacks")
    if not (folder / "compose.yaml").is_file():
        raise NexaHomeError(f"no such stack: {name}", "nexahome stacks")
    doomed: list[str] = []
    for where, folders, names in os.walk(folder, followlinks=False):
        for entry in [*folders, *names]:
            if os.path.islink(os.path.join(where, entry)):
                raise NexaHomeError(f"{shown} contains a link ({entry}); remove will not follow or delete it", f"ls -la {shown}")
        doomed += [str(Path(where, entry).relative_to(instance)) for entry in names]
    if folder.is_symlink():
        raise NexaHomeError(f"{shown} is a link; remove will not follow it", f"ls -la {shown}")
    compose_file = folder / "compose.yaml"
    state = compose.stack_state(ctx, compose_file)
    if state == "running":
        raise NexaHomeError(f"{shown} is running; stop it first", f"docker compose -f {ctx.display(compose_file)} down")
    settings = config.read(instance)
    listed = list(settings.stacks) if settings else []
    remaining = [entry for entry in listed if entry != name]
    if name in listed and not remaining:
        raise NexaHomeError(f"{shown} is the only stack in nexahome.toml, and the list cannot be empty", "nexahome config set stacks hello")
    print(f"This deletes {shown} and everything in it:", file=ctx.out)
    for file in sorted(doomed):
        print(f"  {file}", file=ctx.out)
    if state == "unknown":
        print("Docker did not answer, so nexahome could not tell whether it is running. Stop it first if it is.", file=ctx.out)
    print(f"Docker volumes are not deleted. List them: docker volume ls --filter label=com.docker.compose.project=nexahome-{name}", file=ctx.out)
    if not assume_yes:
        answer = ctx.ask(f"Delete {shown}? [y/N] ")
        if answer is None:
            raise NexaHomeError("cannot ask: input is not a terminal", f"nexahome stacks remove {name} --yes")
        if not answer:
            print("nothing was removed", file=ctx.out)
            return False
    if name in listed:
        config.write(instance, remaining)
    try:
        shutil.rmtree(folder)
    except OSError as error:
        raise NexaHomeError(f"{shown} is no longer in nexahome.toml but could not be deleted: {error}", f"rm -r {shown}") from error
    print(f"removed {shown}", file=ctx.out)
    return True
