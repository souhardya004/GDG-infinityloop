"""Shared regex helpers for C-like and scripting languages without full grammars."""

from __future__ import annotations

import re

from apps.parsers.ir import IRImport, IRSymbol

IMPORT_PATTERNS: dict[str, re.Pattern[str]] = {
    "java": re.compile(r"^import\s+([\w.]+)\s*;", re.MULTILINE),
    "go": re.compile(r"""^\s*(?:import\s+(?:"([^"]+)"|`([^`]+)`)|"([^"]+)")""", re.MULTILINE),
    "csharp": re.compile(r"^using\s+([\w.]+)\s*;", re.MULTILINE),
    "cpp": re.compile(r'^#\s*include\s*[<"]([^>"]+)[>"]', re.MULTILINE),
    "php": re.compile(r"^(?:use|require(?:_once)?|include(?:_once)?)\s+([^;]+);", re.MULTILINE),
}

CLASS_PATTERNS: dict[str, re.Pattern[str]] = {
    "java": re.compile(
        r"^(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
        re.MULTILINE,
    ),
    "go": re.compile(r"^type\s+(\w+)\s+struct\b", re.MULTILINE),
    "csharp": re.compile(
        r"^(?:public\s+|internal\s+|private\s+)?(?:abstract\s+|sealed\s+|static\s+)?class\s+(\w+)(?:\s*:\s*([\w,\s]+))?",
        re.MULTILINE,
    ),
    "cpp": re.compile(r"^(?:class|struct)\s+(\w+)(?:\s*:\s*[^{]+)?", re.MULTILINE),
    "php": re.compile(
        r"^(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
        re.MULTILINE,
    ),
}

FUNC_PATTERNS: dict[str, re.Pattern[str]] = {
    "java": re.compile(
        r"^(?:public|protected|private|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^;]*\)\s*\{",
        re.MULTILINE,
    ),
    "go": re.compile(r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(", re.MULTILINE),
    "csharp": re.compile(
        r"^(?:public|private|protected|internal|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^;]*\)\s*\{",
        re.MULTILINE,
    ),
    "cpp": re.compile(r"^[\w:\s*&<>]+\s+(\w+)\s*\([^;]*\)\s*\{", re.MULTILINE),
    "php": re.compile(
        r"^(?:public|private|protected|static|\s)*function\s+(\w+)\s*\(",
        re.MULTILINE,
    ),
}


def extract_basic_ir(language: str, path: str, text: str) -> tuple[list[IRImport], list[IRSymbol]]:
    module_name = path.replace("\\", "/").rsplit(".", 1)[0].replace("/", ".")
    imports: list[IRImport] = []
    symbols: list[IRSymbol] = []

    import_re = IMPORT_PATTERNS.get(language)
    if import_re:
        for match in import_re.finditer(text):
            module = next((g for g in match.groups() if g), "")
            if module:
                line = text[: match.start()].count("\n") + 1
                imports.append(IRImport(module=module.strip().strip("'\""), names=[], line=line))

    class_re = CLASS_PATTERNS.get(language)
    if class_re:
        for match in class_re.finditer(text):
            line = text[: match.start()].count("\n") + 1
            bases = []
            if match.lastindex and match.lastindex >= 2 and match.group(2):
                bases = [b.strip() for b in match.group(2).split(",") if b.strip()]
            symbols.append(
                IRSymbol(
                    kind="class",
                    name=match.group(1),
                    qualified_name=f"{module_name}:{match.group(1)}",
                    line_start=line,
                    line_end=line,
                    bases=bases,
                )
            )

    func_re = FUNC_PATTERNS.get(language)
    if func_re:
        for match in func_re.finditer(text):
            name = match.group(1)
            if name in {"if", "for", "while", "switch", "catch", "new"}:
                continue
            line = text[: match.start()].count("\n") + 1
            symbols.append(
                IRSymbol(
                    kind="function",
                    name=name,
                    qualified_name=f"{module_name}:{name}",
                    line_start=line,
                    line_end=line,
                )
            )

    return imports, symbols
