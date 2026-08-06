"""TypeScript parser — extends JavaScript heuristics with type-only imports."""

from __future__ import annotations

from typing import ClassVar

from apps.parsers.ir import IRFile
from apps.parsers.languages.javascript import JavaScriptParser


class TypeScriptParser(JavaScriptParser):
    name: ClassVar[str] = "typescript"
    languages: ClassVar[frozenset[str]] = frozenset({"typescript"})
    extensions: ClassVar[frozenset[str]] = frozenset({".ts", ".tsx", ".mts", ".cts"})
    priority: ClassVar[int] = 150

    def parse(self, path: str, source: bytes) -> IRFile:
        result = super().parse(path, source)
        result.language = "typescript"
        return result
