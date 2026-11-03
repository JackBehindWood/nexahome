"""defaults.py holds literals only (D1): no import, no logic, so loading it costs one small module."""

import ast
from pathlib import Path

import nexahome.defaults as defaults

TREE = ast.parse(Path(defaults.__file__).read_text())
ARITHMETIC = (ast.Constant, ast.BinOp, ast.UnaryOp, ast.Tuple, ast.operator, ast.unaryop, ast.Load)


def test_the_module_has_only_documented_upper_case_literals() -> None:
    body = TREE.body
    assert isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)  # the docstring
    for node in body[1:]:
        assert isinstance(node, ast.Assign), f"line {node.lineno}: only assignments"
        assert [t.id for t in node.targets if isinstance(t, ast.Name) and t.id.isupper()], f"line {node.lineno}: UPPER_CASE names"
        assert all(isinstance(part, ARITHMETIC) for part in ast.walk(node.value)), f"line {node.lineno}: a literal, not logic"


def test_the_module_imports_nothing() -> None:
    assert not [n for n in ast.walk(TREE) if isinstance(n, (ast.Import, ast.ImportFrom))]


def test_every_constant_is_used_somewhere_else() -> None:
    source = "\n".join(p.read_text() for p in Path(defaults.__file__).parent.rglob("*.py") if p.name != "defaults.py")
    unused = [name for name in vars(defaults) if name.isupper() and name not in source]
    assert unused == []
