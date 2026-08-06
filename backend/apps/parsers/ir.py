"""Intermediate representation shared by all language parsers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IRParameter:
    name: str
    type_annotation: str | None = None
    default: str | None = None


@dataclass
class IRCall:
    callee: str
    line: int
    is_await: bool = False


@dataclass
class IRImport:
    module: str
    names: list[str] = field(default_factory=list)
    is_relative: bool = False
    line: int = 0
    resolved_path: str | None = None


@dataclass
class IRSymbol:
    kind: str  # function | class | method | field | variable | interface
    name: str
    qualified_name: str
    line_start: int
    line_end: int
    bases: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    parameters: list[IRParameter] = field(default_factory=list)
    return_type: str | None = None
    is_async: bool = False
    is_static: bool = False
    docstring: str | None = None
    calls: list[IRCall] = field(default_factory=list)


@dataclass
class IRFile:
    path: str
    language: str
    content_hash: str
    imports: list[IRImport] = field(default_factory=list)
    symbols: list[IRSymbol] = field(default_factory=list)
