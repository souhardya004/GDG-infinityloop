"""JavaScript parser using regex/heuristic AST-lite extraction.

Tree-sitter grammars are optional; this implementation extracts imports,
functions, and classes reliably for visualization without a native grammar build.
"""

from __future__ import annotations

import re
from typing import ClassVar

from apps.parsers.base import ParserPlugin
from apps.parsers.ir import IRCall, IRFile, IRImport, IRSymbol

_IMPORT_RE = re.compile(
    r"""^import\s+(?:type\s+)?(?:([\w*\s{},]+)\s+from\s+)?['"]([^'"]+)['"]""",
    re.MULTILINE,
)
_REQUIRE_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
_FUNC_RE = re.compile(
    r"""^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)""",
    re.MULTILINE,
)
_ARROW_RE = re.compile(
    r"""^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>""",
    re.MULTILINE,
)
_CLASS_RE = re.compile(
    r"""^(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?""",
    re.MULTILINE,
)
_CALL_RE = re.compile(r"""\b([A-Za-z_][\w.]*)\s*\(""")


class JavaScriptParser(ParserPlugin):
    name: ClassVar[str] = "javascript"
    languages: ClassVar[frozenset[str]] = frozenset({"javascript"})
    extensions: ClassVar[frozenset[str]] = frozenset({".js", ".jsx", ".mjs", ".cjs"})
    priority: ClassVar[int] = 100

    def parse(self, path: str, source: bytes) -> IRFile:
        text = source.decode("utf-8", errors="replace")
        lines = text.splitlines()
        module_name = path.replace("\\", "/").rsplit(".", 1)[0].replace("/", ".")

        imports: list[IRImport] = []
        for match in _IMPORT_RE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            names_raw = (match.group(1) or "").strip()
            names = [n.strip() for n in re.split(r"[{},]", names_raw) if n.strip() and n.strip() != "*"]
            imports.append(IRImport(module=match.group(2), names=names, line=line))
        for match in _REQUIRE_RE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            imports.append(IRImport(module=match.group(1), names=[], line=line))

        symbols: list[IRSymbol] = []
        for match in _FUNC_RE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            name = match.group(1)
            params = [p.strip().split("=")[0].strip() for p in match.group(2).split(",") if p.strip()]
            body_calls = [
                IRCall(callee=c.group(1), line=line)
                for c in _CALL_RE.finditer(_window(lines, line, 40))
                if c.group(1) != name
            ]
            symbols.append(
                IRSymbol(
                    kind="function",
                    name=name,
                    qualified_name=f"{module_name}:{name}",
                    line_start=line,
                    line_end=line,
                    parameters=[],
                    calls=body_calls[:50],
                    is_async="async function" in match.group(0),
                )
            )
            # attach param names without types
            from apps.parsers.ir import IRParameter

            symbols[-1].parameters = [IRParameter(name=p) for p in params]

        for match in _ARROW_RE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            name = match.group(1)
            symbols.append(
                IRSymbol(
                    kind="function",
                    name=name,
                    qualified_name=f"{module_name}:{name}",
                    line_start=line,
                    line_end=line,
                )
            )

        for match in _CLASS_RE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            bases = [match.group(2)] if match.group(2) else []
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

        return IRFile(
            path=path,
            language="javascript",
            content_hash=self.content_hash(source),
            imports=imports,
            symbols=symbols,
        )


def _window(lines: list[str], start_line: int, size: int) -> str:
    start = max(0, start_line - 1)
    return "\n".join(lines[start : start + size])
