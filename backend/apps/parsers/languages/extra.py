from __future__ import annotations

from typing import ClassVar

from apps.parsers.base import ParserPlugin
from apps.parsers.ir import IRFile
from apps.parsers.languages.basic import extract_basic_ir


class _BasicLanguageParser(ParserPlugin):
    language_id: ClassVar[str]

    def parse(self, path: str, source: bytes) -> IRFile:
        text = source.decode("utf-8", errors="replace")
        imports, symbols = extract_basic_ir(self.language_id, path, text)
        return IRFile(
            path=path,
            language=self.language_id,
            content_hash=self.content_hash(source),
            imports=imports,
            symbols=symbols,
        )


class JavaParser(_BasicLanguageParser):
    name: ClassVar[str] = "java"
    language_id: ClassVar[str] = "java"
    languages: ClassVar[frozenset[str]] = frozenset({"java"})
    extensions: ClassVar[frozenset[str]] = frozenset({".java"})
    priority: ClassVar[int] = 100


class GoParser(_BasicLanguageParser):
    name: ClassVar[str] = "go"
    language_id: ClassVar[str] = "go"
    languages: ClassVar[frozenset[str]] = frozenset({"go"})
    extensions: ClassVar[frozenset[str]] = frozenset({".go"})
    priority: ClassVar[int] = 100


class CSharpParser(_BasicLanguageParser):
    name: ClassVar[str] = "csharp"
    language_id: ClassVar[str] = "csharp"
    languages: ClassVar[frozenset[str]] = frozenset({"csharp"})
    extensions: ClassVar[frozenset[str]] = frozenset({".cs"})
    priority: ClassVar[int] = 100


class CppParser(_BasicLanguageParser):
    name: ClassVar[str] = "cpp"
    language_id: ClassVar[str] = "cpp"
    languages: ClassVar[frozenset[str]] = frozenset({"cpp"})
    extensions: ClassVar[frozenset[str]] = frozenset({".cpp", ".cc", ".cxx", ".h", ".hpp"})
    priority: ClassVar[int] = 100


class PhpParser(_BasicLanguageParser):
    name: ClassVar[str] = "php"
    language_id: ClassVar[str] = "php"
    languages: ClassVar[frozenset[str]] = frozenset({"php"})
    extensions: ClassVar[frozenset[str]] = frozenset({".php"})
    priority: ClassVar[int] = 100
