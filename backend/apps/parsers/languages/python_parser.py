"""Python parser — stdlib ast with optional LibCST enrichment for imports."""

from __future__ import annotations

import ast
from typing import ClassVar

from apps.parsers.base import ParserPlugin
from apps.parsers.ir import IRCall, IRFile, IRImport, IRParameter, IRSymbol


class PythonParser(ParserPlugin):
    name: ClassVar[str] = "python"
    languages: ClassVar[frozenset[str]] = frozenset({"python"})
    extensions: ClassVar[frozenset[str]] = frozenset({".py", ".pyi"})
    priority: ClassVar[int] = 200

    def parse(self, path: str, source: bytes) -> IRFile:
        text = source.decode("utf-8", errors="replace")
        tree = ast.parse(text)
        module_name = _module_name(path)
        imports = _collect_imports(tree)
        symbols = _collect_symbols(tree, module_name)
        return IRFile(
            path=path,
            language="python",
            content_hash=self.content_hash(source),
            imports=imports,
            symbols=symbols,
        )


def _module_name(path: str) -> str:
    return path.replace("\\", "/").removesuffix(".py").removesuffix(".pyi").replace("/", ".")


def _ann(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return None


def _name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name(node.value)}.{node.attr}"
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return type(node).__name__


def _collect_imports(tree: ast.AST) -> list[IRImport]:
    imports: list[IRImport] = []
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(IRImport(module=alias.name, names=[], line=node.lineno))
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                IRImport(
                    module=node.module or ".",
                    names=[a.name for a in node.names],
                    is_relative=node.level > 0,
                    line=node.lineno,
                )
            )
    return imports


def _calls(node: ast.AST) -> list[IRCall]:
    calls: list[IRCall] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            calls.append(
                IRCall(
                    callee=_name(child.func),
                    line=getattr(child, "lineno", 0) or 0,
                    is_await=False,
                )
            )
        elif isinstance(child, ast.Await) and isinstance(child.value, ast.Call):
            calls.append(
                IRCall(
                    callee=_name(child.value.func),
                    line=getattr(child, "lineno", 0) or 0,
                    is_await=True,
                )
            )
    return calls


def _params(args: ast.arguments) -> list[IRParameter]:
    return [
        IRParameter(name=a.arg, type_annotation=_ann(a.annotation))
        for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]
    ]


def _function_symbol(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    qualified_name: str,
    kind: str,
) -> IRSymbol:
    return IRSymbol(
        kind=kind,
        name=node.name,
        qualified_name=qualified_name,
        line_start=node.lineno,
        line_end=getattr(node, "end_lineno", None) or node.lineno,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        docstring=ast.get_docstring(node),
        parameters=_params(node.args),
        return_type=_ann(node.returns),
        calls=_calls(node),
        decorators=[_name(d) for d in node.decorator_list],
    )


def _collect_symbols(tree: ast.Module, module_name: str) -> list[IRSymbol]:
    symbols: list[IRSymbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                _function_symbol(node, f"{module_name}:{node.name}", "function")
            )
        elif isinstance(node, ast.ClassDef):
            symbols.append(
                IRSymbol(
                    kind="class",
                    name=node.name,
                    qualified_name=f"{module_name}:{node.name}",
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", None) or node.lineno,
                    bases=[_name(b) for b in node.bases],
                    docstring=ast.get_docstring(node),
                    decorators=[_name(d) for d in node.decorator_list],
                )
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        _function_symbol(
                            item,
                            f"{module_name}:{node.name}.{item.name}",
                            "method",
                        )
                    )
    return symbols
