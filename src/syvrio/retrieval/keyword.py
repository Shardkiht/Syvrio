from __future__ import annotations

import logging
import math
import re
from functools import lru_cache
from unicodedata import normalize

from rank_bm25 import BM25Okapi

from ..memory.models import Entry, short_field
from ..memory.store import MemoryStore
from .base import SearchHit

try:
    import jieba

    jieba.setLogLevel(logging.ERROR)
except ImportError:  # pragma: no cover - 依赖缺失时退回字符二元组
    jieba = None


def _is_word(token: str) -> bool:
    return any(char.isalnum() or "\u4e00" <= char <= "\u9fff" for char in token)


# 封闭的虚词表：这类词几乎无检索信号，却让任何查询都能虚匹配出低分结果，
# 混合检索时这些噪声条目会被 RRF 当成"两路都出现"而放大（evals/ 有量化对比）。
STOPWORDS = frozenset(
    "的 了 着 是 在 我 你 他 她 它 我们 你们 他们 和 与 就 也 都 而 及 或 等 啊 呢 吧 吗 呀 嘛".split()
)


@lru_cache(maxsize=4096)
def tokenize(text: str) -> tuple[str, ...]:
    if jieba is not None:
        tokens = [token.strip().lower() for token in jieba.lcut_for_search(text)]
    else:
        lowered = text.lower()
        tokens = [lowered[index : index + 2] for index in range(max(1, len(lowered) - 1))]
    return tuple(
        token for token in tokens if token and _is_word(token) and token not in STOPWORDS
    )


def _field_key(text: str) -> str:
    return " ".join(normalize("NFKC", text).casefold().split())


def _query_field_labels(query: str, fields: dict[str, list[int]]) -> set[str]:
    """Match complete label spans and suppress labels nested inside a longer one."""
    query = _field_key(query)
    if jieba is not None:
        tokens = tuple(jieba.tokenize(query))
        starts = {start for _, start, _ in tokens}
        ends = {end for _, _, end in tokens}
    else:  # pragma: no cover - jieba is a required dependency
        tokens = tuple(re.finditer(r"[a-z0-9_]+|[^a-z0-9_]", query))
        starts = {token.start() for token in tokens}
        ends = {token.end() for token in tokens}
    spans = []
    for label in fields:
        for match in re.finditer(re.escape(label), query):
            start, end = match.span()
            if start in starts and end in ends:
                spans.append((start, end, label))
    selected: set[str] = set()
    covered: set[int] = set()
    for start, end, label in sorted(spans, key=lambda span: (span[0] - span[1], span[0])):
        positions = range(start, end)
        if covered.isdisjoint(positions):
            selected.add(label)
            covered.update(positions)
    return selected


class KeywordRetriever:
    def __init__(self, store: MemoryStore, k1: float = 1.5, b: float = 0.75):
        self.store = store
        self.k1 = k1
        self.b = b
        self._entries: list[Entry] = []
        self._bm25: BM25Okapi | None = None
        self._fields: dict[str, list[int]] = {}
        self._fingerprint: tuple[tuple[str, str], ...] | None = None

    def _index(self) -> tuple[list[Entry], BM25Okapi | None]:
        fingerprint = self.store.fingerprint()
        if self._bm25 is None or fingerprint != self._fingerprint:
            self._entries = self.store.entries()
            self._fields = {}
            for index, entry in enumerate(self._entries):
                if field := short_field(entry.text):
                    self._fields.setdefault(_field_key(field[0]), []).append(index)
            corpus = [list(tokenize(entry.index_text)) for entry in self._entries]
            self._bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b) if any(corpus) else None
            if self._bm25 is not None:
                # Okapi 的负 IDF 会让小库的相关结果全部被过滤；使用正值的平滑 IDF。
                frequencies: dict[str, int] = {}
                for document in corpus:
                    for token in set(document):
                        frequencies[token] = frequencies.get(token, 0) + 1
                self._bm25.idf = {
                    token: math.log1p((len(corpus) - count + 0.5) / (count + 0.5))
                    for token, count in frequencies.items()
                }
            self._fingerprint = fingerprint
        return self._entries, self._bm25

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        query = query.strip()
        if not query:
            return []
        entries, bm25 = self._index()
        if not entries or bm25 is None:
            return []
        query_tokens = list(tokenize(query))
        if not query_tokens:
            return []

        scores = bm25.get_scores(query_tokens)
        labels = _query_field_labels(query, self._fields) if self._fields else set()
        fields = {index: label for label in labels for index in self._fields[label]}
        lowered = query.lower()
        ranked = sorted(
            (
                (index in fields,
                 score + (2.0 if lowered in entry.index_text.lower() else 0.0), index)
                for index, (entry, score) in enumerate(zip(entries, scores))
            ),
            reverse=True,
        )
        return [
            SearchHit(
                id=entries[index].id,
                file=str(self.store.topic_path(entries[index].topic)),
                source_path=entries[index].source_path,
                line=entries[index].line,
                end_line=entries[index].end_line,
                raw_markdown=entries[index].raw_markdown,
                index_text=entries[index].index_text,
                text=entries[index].text,
                topic=entries[index].topic,
                timestamp=entries[index].timestamp,
                score=round(max(float(score), 0.0), 4),
                matched_field=fields.get(index, ""),
            )
            for exact, score, index in ranked[:limit]
            if exact or score > 0
        ]
