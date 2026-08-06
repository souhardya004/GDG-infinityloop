"""Language detection helpers."""

from __future__ import annotations

from pathlib import Path

LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".java": "java",
    ".go": "go",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".php": "php",
}

SUPPORTED_LANGUAGES = frozenset(LANGUAGE_EXTENSIONS.values())


def detect_language(relative_path: str) -> str | None:
    suffix = Path(relative_path).suffix.lower()
    return LANGUAGE_EXTENSIONS.get(suffix)


def is_probably_test(relative_path: str) -> bool:
    path = relative_path.replace("\\", "/").lower()
    name = Path(path).name
    return (
        "/tests/" in f"/{path}"
        or "/__tests__/" in f"/{path}"
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.js")
        or name.endswith(".test.ts")
        or name.endswith(".spec.js")
        or name.endswith(".spec.ts")
    )


def is_probably_generated(relative_path: str) -> bool:
    path = relative_path.replace("\\", "/").lower()
    markers = (
        "/node_modules/",
        "/.git/",
        "/dist/",
        "/build/",
        "/__pycache__/",
        "/.venv/",
        "/venv/",
        "/vendor/",
        "/target/",
    )
    return any(m in f"/{path}" for m in markers)
