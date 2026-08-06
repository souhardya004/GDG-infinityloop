"""Parser plugin protocol and base helpers."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import ClassVar

from apps.parsers.ir import IRFile


class ParserPlugin(ABC):
    name: ClassVar[str]
    languages: ClassVar[frozenset[str]]
    extensions: ClassVar[frozenset[str]]
    priority: ClassVar[int] = 100

    def supports(self, path: str, language: str | None = None) -> bool:
        lowered = path.lower()
        if language and language in self.languages:
            return True
        return any(lowered.endswith(ext) for ext in self.extensions)

    @abstractmethod
    def parse(self, path: str, source: bytes) -> IRFile:
        raise NotImplementedError

    @staticmethod
    def content_hash(source: bytes) -> str:
        return hashlib.sha256(source).hexdigest()
