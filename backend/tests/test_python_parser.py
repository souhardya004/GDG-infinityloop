"""Smoke test for Python parser IR extraction."""

from apps.parsers.languages.python_parser import PythonParser


def test_python_parser_extracts_function_and_import():
    source = b'''
import os
from pathlib import Path

class Greeter:
    def hello(self, name: str) -> str:
        return f"hi {name}"

def run():
    return Greeter().hello("world")
'''
    ir = PythonParser().parse("src/app.py", source)
    assert ir.language == "python"
    assert any(i.module == "os" for i in ir.imports)
    assert any(i.module == "pathlib" for i in ir.imports)
    names = {s.qualified_name for s in ir.symbols}
    assert "src.app:Greeter" in names
    assert "src.app:run" in names
    assert "src.app:Greeter.hello" in names
