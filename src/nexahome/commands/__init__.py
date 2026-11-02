"""The registered commands. To add one: a module here with NAME, register() and run(), one line in COMMANDS."""

from nexahome.commands import doctor
from nexahome.commands.base import Command

COMMANDS: tuple[Command, ...] = (doctor,)
