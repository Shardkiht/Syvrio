from __future__ import annotations

import pytest

pytestmark = pytest.mark.retrieval

import numpy as np

from syvrio.infra.config import Config, EmbeddingConfig, RetrievalConfig
from syvrio.memory import service as service_module
from syvrio.memory.store import MemoryStore
from syvrio.retrieval import (
    HybridRetriever,
    KeywordRetriever,
    SearchHit,
    VectorRetriever,
)

# 同义词组：组内任一词命中即贡献该维度方向，模拟语义相近。
GROUPS = {
    "housing": ["房", "住", "租"],
    "coffee": ["咖啡", "清淡", "茶"],
    "work": ["工作", "后端"],
}


class FakeEmbedder:
    """确定性假 Embedder；记录条目/查询侧调用，fail=True 模拟后端不可用。"""

    def __init__(self, groups: dict[str, list[str]], model_id: str = "fake", fail: bool = False):
        self.model_id = model_id
        self.groups = groups
        self.fail = fail
        self.passages: list[str] = []
        self.queries: list[str] = []

    def _vector(self, text: str) -> list[float]:
        if self.fail:
            raise RuntimeError("embedding 不可用")
        vector = np.zeros(len(self.groups), dtype=np.float32)
        for index, words in enumerate(self.groups.values()):
            if any(word in text for word in words):
                vector[index] = 1.0
        return vector.tolist()

    def embed(self, texts) -> list[list[float]]:
        self.passages.extend(texts)
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return self._vector(text)


def seeded_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path)
    store.append("housing", "在找市区的房子，预算 4000 以内")
    store.append("preferences", "咖啡偏好清淡、像茶的风味")
    return store


def test_vector_search_finds_paraphrase(tmp_path):
    store = seeded_store(tmp_path)
    retriever = VectorRetriever(store, FakeEmbedder(GROUPS))

    hits = retriever.search("住的地方", limit=3)

    assert hits and hits[0].topic == "memories/general/housing.md"


def test_incremental_sync_embeds_only_new_entries(tmp_path):
    store = seeded_store(tmp_path)
    embedder = FakeEmbedder(GROUPS)
    retriever = VectorRetriever(store, embedder)

    retriever.search("房子", 3)
    assert len(embedder.passages) == 2
    retriever.search("房子", 3)
    assert len(embedder.passages) == 2

    store.append("career", "在找后端工作")
    retriever.search("工作", 3)
    assert len(embedder.passages) == 3


def test_cache_persists_across_instances(tmp_path):
    store = seeded_store(tmp_path)
    VectorRetriever(store, FakeEmbedder(GROUPS)).search("房子", 3)

    embedder = FakeEmbedder(GROUPS)
    retriever = VectorRetriever(store, embedder)
    assert retriever.search("房子", 3)
    assert embedder.passages == []


def test_model_change_rebuilds_cache(tmp_path):
    store = seeded_store(tmp_path)
    VectorRetriever(store, FakeEmbedder(GROUPS, model_id="fake-a")).search("房子", 3)

    embedder = FakeEmbedder(GROUPS, model_id="fake-b")
    retriever = VectorRetriever(store, embedder)
    assert retriever.search("房子", 3)
    assert len(embedder.passages) == 2


def test_vector_search_degrades_to_empty_when_embedder_fails(tmp_path):
    store = seeded_store(tmp_path)
    retriever = VectorRetriever(store, FakeEmbedder(GROUPS, fail=True))

    assert retriever.search("房子", 3) == []


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_sync_retries_after_embedding_failure(tmp_path):
    from syvrio.retrieval.vector import RETRY_COOLDOWN_SECONDS

    clock = FakeClock()
    store = seeded_store(tmp_path)
    embedder = FakeEmbedder(GROUPS, fail=True)
    retriever = VectorRetriever(store, embedder, clock=clock)
    assert retriever.search("房子", 3) == []
    assert retriever.degraded is True
    passage_calls = len(embedder.passages)

    # 冷却期内不重复打后端，避免每次检索都卡在失败调用上。
    embedder.fail = False
    assert retriever.search("房子", 3) == []
    assert len(embedder.passages) == passage_calls

    # 冷却到期后即使记忆文件没变也要重新同步，而不是一直返回空。
    clock.now += RETRY_COOLDOWN_SECONDS
    hits = retriever.search("房子", 3)
    assert hits and hits[0].topic == "memories/general/housing.md"
    assert retriever.degraded is False


def test_query_failure_enters_cooldown(tmp_path):
    from syvrio.retrieval.vector import RETRY_COOLDOWN_SECONDS

    clock = FakeClock()
    store = seeded_store(tmp_path)
    embedder = FakeEmbedder(GROUPS)
    retriever = VectorRetriever(store, embedder, clock=clock)
    assert retriever.search("房子", 3)

    embedder.fail = True
    assert retriever.search("房子", 3) == []
    assert retriever.degraded is True
    query_calls = len(embedder.queries)

    embedder.fail = False
    assert retriever.search("房子", 3) == []
    assert len(embedder.queries) == query_calls

    clock.now += RETRY_COOLDOWN_SECONDS
    assert retriever.search("房子", 3)
    assert retriever.degraded is False


def test_search_ignores_deleted_entries(tmp_path):
    store = seeded_store(tmp_path)
    entry = store.append("career", "在找后端工作")
    retriever = VectorRetriever(store, FakeEmbedder(GROUPS))
    assert retriever.search("后端", 3)

    store.set_status(entry.id, "deleted")
    assert all(hit.id != entry.id for hit in retriever.search("后端", 3))


class StubRetriever:
    def __init__(self, ids: list[str]):
        self.ids = ids

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        return [SearchHit(id=i, text=f"text-{i}", topic="t") for i in self.ids[:limit]]


def test_hybrid_ranks_hits_in_both_paths_first():
    # 夹具需通过字面覆盖闸（查询 bigram 在条目中覆盖率 >= 0.3）
    keyword = StubRetriever(["红轴机械键盘", "键盘轴体", "红轴与键盘手感"])
    vector = StubRetriever(["键盘轴体", "桌面音箱"])
    hits = HybridRetriever(keyword, vector).search("红轴键盘", limit=3)

    assert hits[0].id == "键盘轴体"
    assert len(hits) == 3


def test_hybrid_breaks_rrf_ties_toward_vector_rank():
    # BM25 噪声把 a 排第一、c 排第三；向量把 c 排第一、a 排第三 → RRF 完全平局，
    # 决胜应信任向量名次（c 第一）。夹具全部含查询词"键盘"，通过字面覆盖闸。
    keyword = StubRetriever(["键盘手感", "键盘轴体", "机械键盘套装"])
    vector = StubRetriever(["机械键盘套装", "键盘轴体", "键盘手感"])
    hits = HybridRetriever(keyword, vector).search("键盘", limit=3)

    assert [hit.id for hit in hits[:2]] == ["机械键盘套装", "键盘手感"]


def test_hybrid_falls_back_to_keyword_when_vector_fails(tmp_path):
    store = seeded_store(tmp_path)
    hybrid = HybridRetriever(
        KeywordRetriever(store),
        VectorRetriever(store, FakeEmbedder(GROUPS, fail=True)),
    )

    hits = hybrid.search("咖啡", limit=3)

    assert hits and hits[0].topic == "memories/general/preferences.md"


def test_literal_coverage_does_not_join_words_across_separators():
    from syvrio.memory.detect import bigram_coverage

    assert bigram_coverage("姓名，年龄", "姓名") == 0.5
    assert bigram_coverage("姓名 年龄", "姓名 年龄") == 1.0
    assert bigram_coverage("名年", "姓名 年龄") == 0.0


def test_short_field_coverage_keeps_exact_hit_without_restoring_noise(tmp_path):
    store = MemoryStore(tmp_path)
    name = store.append("identity", "姓名：虚构人物甲", title="合成人物资料")
    noise = store.append("archive", "登记规则会核验称呼，并检查活动报名材料")
    competing = store.append("archive", "登山装备清单")
    query = "姓名 名字 称呼 身份"

    class SemanticHits:
        def search(self, query, limit):
            return [SearchHit(id=competing.id, text=competing.text, topic=competing.topic)]

    keyword = KeywordRetriever(store)
    assert noise.id in {hit.id for hit in keyword.search(query)}
    hits = HybridRetriever(keyword, SemanticHits()).search(query)
    assert [hit.id for hit in hits] == [name.id, competing.id]
    assert hits[0].raw_markdown == name.raw_markdown
    assert (hits[0].source_path, hits[0].line) == (name.source_path, name.line)


def test_embedding_cache_rebuilds_changed_short_fact_only(tmp_path):
    from syvrio.retrieval.vector import text_hash

    store = MemoryStore(tmp_path)
    short = store.append("identity", "姓名：虚构人物甲", title="合成人物资料")
    long = store.append("preferences", "我喜欢清淡的咖啡，有时也会喝茶")
    embedder = FakeEmbedder({"name": ["姓名"], **GROUPS})
    vector = VectorRetriever(store, embedder)
    vector.cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        vector.cache_path, model=np.array(embedder.model_id),
        ids=np.array([short.id, long.id]),
        hashes=np.array([text_hash(short.index_text), text_hash(long.index_text)]),
        vectors=np.array([[1., 0., 0., 0.], [0., 0., 1., 0.]]),
    )
    assert short.embedding_text != short.index_text
    assert "合成人物资料" in short.embedding_text
    assert long.embedding_text == long.index_text
    assert vector.search("姓名")[0].id == short.id
    assert embedder.passages == [short.embedding_text]
    assert store.find(short.id).raw_markdown == short.raw_markdown

    path = store.topic_path(short.topic)
    path.write_text(path.read_text().replace("# 合成人物资料", "# 演示身份档案"))
    embedder.passages.clear()
    vector.sync()
    updated = store.find(short.id)
    assert embedder.passages == [updated.embedding_text]
    assert updated.raw_markdown == short.raw_markdown


def test_large_corpus_keeps_explicit_short_fields_without_local_model(tmp_path):
    from evals.short_facts_eval import SHORT_CASES, seed_vault

    assert seed_vault(tmp_path) >= 1200
    store = MemoryStore(tmp_path)
    keyword = KeywordRetriever(store)

    class DistractingVector:
        def search(self, query, limit):
            return [
                SearchHit(id=f"distractor-{n:04}", text="同领域干扰", topic="archive")
                for n in range(min(limit, 80))
            ]

    hybrid = HybridRetriever(keyword, DistractingVector())
    for field, query in SHORT_CASES:
        if query in {"我是谁", "我叫什么名字"}:
            continue  # These require query rewriting or semantic embeddings.
        assert f"short-{field}" in {hit.id for hit in hybrid.search(query, 3)}, query


def test_build_retriever_falls_back_without_fastembed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        service_module.LocalEmbedder, "available", staticmethod(lambda: False)
    )
    config = Config(vault=tmp_path, retrieval=RetrievalConfig(method="hybrid"))

    retriever, mode = service_module.build_retriever(config, MemoryStore(tmp_path))

    assert isinstance(retriever, KeywordRetriever)
    assert mode == "hybrid-fallback-keyword"


def test_build_retriever_hybrid_when_local_available(tmp_path, monkeypatch):
    monkeypatch.setattr(
        service_module.LocalEmbedder, "available", staticmethod(lambda: True)
    )
    config = Config(vault=tmp_path, retrieval=RetrievalConfig(method="hybrid"))

    retriever, mode = service_module.build_retriever(config, MemoryStore(tmp_path))

    assert isinstance(retriever, HybridRetriever)
    assert mode == "hybrid"
    assert isinstance(retriever.vector.embedder.model_id, str)


def test_build_retriever_api_backend(tmp_path, monkeypatch):
    config = Config(
        vault=tmp_path,
        retrieval=RetrievalConfig(
            method="hybrid",
            embedding=EmbeddingConfig(
                backend="api", model="BAAI/bge-m3", api_key_env="TEST_EMBED_KEY"
            ),
        ),
    )
    monkeypatch.setenv("TEST_EMBED_KEY", "test-key")
    retriever, mode = service_module.build_retriever(config, MemoryStore(tmp_path))
    assert mode == "hybrid"

    monkeypatch.delenv("TEST_EMBED_KEY")
    retriever, mode = service_module.build_retriever(config, MemoryStore(tmp_path))
    assert isinstance(retriever, KeywordRetriever)
    assert mode == "hybrid-fallback-keyword"


def test_vector_cache_is_outside_vault_git_worktree(tmp_path):
    from syvrio.memory.service import MemoryService

    config = Config(vault=tmp_path / "vault", retrieval=RetrievalConfig(method="keyword"))
    service = MemoryService(config)
    service.init_vault()
    service.note("喜欢清淡、像茶的风味")
    service.commit(push=False)
    retriever = VectorRetriever(service.store, FakeEmbedder(GROUPS))
    retriever.sync()
    assert retriever.cache_path == service.paths.runtime_dir / "indexes" / "vectors.npz"
    assert retriever.cache_path.is_file()
    assert not service.repo.has_changes()
    assert not (config.vault / ".syvrio").exists()


def test_init_vault_preserves_user_gitignore_without_final_newline(tmp_path):
    from syvrio.memory.service import MemoryService

    config = Config(vault=tmp_path / "vault", retrieval=RetrievalConfig(method="keyword"))
    service = MemoryService(config)
    service.store.ensure()
    gitignore = config.vault / ".gitignore"
    gitignore.write_bytes(b"*.log")

    service.init_vault()

    assert gitignore.read_bytes() == b"*.log"


def test_sync_refuses_duplicate_entry_ids_across_topics(tmp_path):
    import pytest
    from syvrio.memory.schema import Core, SchemaError, render_record

    store = MemoryStore(tmp_path)
    store.append("food", "喜欢清淡、像茶的风味", entry_id="mem-dup")
    housing = store.topic_path("housing")
    housing.write_text(render_record("在找市区的房子",
        Core(id="mem-dup", status="active", source="chat", confidence=1.0)), encoding="utf-8")
    retriever = VectorRetriever(store, FakeEmbedder(GROUPS))

    with pytest.raises(SchemaError, match="duplicate memory id across topics"):
        retriever.sync()


def test_malformed_cache_ids_rebuild_instead_of_crashing(tmp_path):
    store = seeded_store(tmp_path)
    retriever = VectorRetriever(store, FakeEmbedder(GROUPS))
    retriever.cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(retriever.cache_path, model=np.array("fake"), ids=np.array([["bad"]]),
             hashes=np.array(["bad"]), vectors=np.ones((1, 3)))
    assert retriever.search("房子")
