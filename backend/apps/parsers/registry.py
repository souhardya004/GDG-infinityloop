"""Parser plugin registry."""

from __future__ import annotations

from apps.parsers.base import ParserPlugin
from apps.parsers.languages.extra import (
    CppParser,
    CSharpParser,
    GoParser,
    JavaParser,
    PhpParser,
)
from apps.parsers.languages.javascript import JavaScriptParser
from apps.parsers.languages.python_parser import PythonParser
from apps.parsers.languages.typescript import TypeScriptParser


class ParserRegistry:
    def __init__(self, plugins: list[ParserPlugin] | None = None) -> None:
        self._plugins = sorted(
            plugins or [],
            key=lambda p: p.priority,
            reverse=True,
        )

    @classmethod
    def default(cls) -> ParserRegistry:
        return cls(
            [
                PythonParser(),
                TypeScriptParser(),
                JavaScriptParser(),
                JavaParser(),
                GoParser(),
                CSharpParser(),
                CppParser(),
                PhpParser(),
            ]
        )

    def resolve(self, path: str, language: str | None = None) -> ParserPlugin | None:
        for plugin in self._plugins:
            if plugin.supports(path, language):
                return plugin
        return None

    def manifests(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "kind": "language",
                "version": "0.1.0",
                "languages": sorted(p.languages),
                "extensions": sorted(p.extensions),
                "priority": p.priority,
            }
            for p in self._plugins
        ]
