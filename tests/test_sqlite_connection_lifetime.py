"""Real SQLite lifetime regressions for evidence storage and corpus retrieval."""

from __future__ import annotations

import gc
import sqlite3
import warnings
from collections.abc import Iterator, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest

from geode.orchestration.services.evidence_store import EvidenceStore
from geode.search import index
from geode.search.db import CorpusRepository, IndexRun
from geode.search.query_index import query_index
from geode.validation.step2_gate import _check_index_run
from tests.test_context_safety import _evidence
from tests.test_search_index import _write_fixture_corpus


class TrackedConnection(sqlite3.Connection):
    """Keep real transactions while recording closure and injecting bounded SQL failures."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize per-connection lifetime observations."""
        super().__init__(*args, **kwargs)
        self.close_calls = 0
        self.fail_sql: str | None = None
        self.fail_exit = False

    def execute(self, sql: str, parameters: Sequence[object] = ()) -> sqlite3.Cursor:
        """Fail a selected statement before SQLite executes it."""
        if self.fail_sql and self.fail_sql in " ".join(sql.split()):
            raise sqlite3.OperationalError("injected statement failure")
        return super().execute(sql, parameters)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Allow testing that connection cleanup survives transaction-exit failure."""
        if self.fail_exit:
            raise sqlite3.OperationalError("injected transaction-exit failure")
        return bool(super().__exit__(exc_type, exc_value, traceback))

    def close(self) -> None:
        """Record explicit close calls, without relying on garbage collection."""
        self.close_calls += 1
        super().close()


@dataclass
class Connections:
    """Retain every connection so garbage collection cannot conceal missing cleanup."""

    opened: list[TrackedConnection] = field(default_factory=list)
    previous_closed_at_open: list[bool] = field(default_factory=list)
    fail_sql: str | None = None
    fail_exit: bool = False

    def assert_closed(self) -> None:
        """Every opened connection must have one explicit close and reject further SQL."""
        assert self.opened
        for connection in self.opened:
            assert connection.close_calls == 1
            with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                sqlite3.Connection.execute(connection, "SELECT 1")


@pytest.fixture
def connections(monkeypatch: pytest.MonkeyPatch) -> Iterator[Connections]:
    """Intercept allocation only; production queries still run on temporary real databases."""
    state = Connections()
    original = sqlite3.connect

    def connect(*args: Any, **kwargs: Any) -> TrackedConnection:
        kwargs["factory"] = TrackedConnection
        connection = original(*args, **kwargs)
        assert isinstance(connection, TrackedConnection)
        connection.fail_sql = state.fail_sql
        connection.fail_exit = state.fail_exit
        state.previous_closed_at_open.append(all(c.close_calls == 1 for c in state.opened))
        state.opened.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    try:
        yield state
    finally:
        # A failing assertion must not itself leave diagnostic fixture connections open.
        for connection in state.opened:
            if not connection.close_calls:
                connection.close()


def _database(tmp_path: Path) -> Path:
    """Build the existing synthetic corpus without accessing preserved source data."""
    root = _write_fixture_corpus(tmp_path)
    path = root / "index.sqlite"
    index.build_index(root, path, rebuild=True)
    return path


def _dump(path: Path) -> list[str]:
    """Read committed logical database content through a separately closed connection."""
    with closing(sqlite3.connect(path)) as connection:
        return list(connection.iterdump())


def test_evidence_constructor_no_longer_emits_resource_warning(tmp_path: Path) -> None:
    """Replay the allocation diagnostic without a connection-retaining test double."""
    gc.collect()
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always", ResourceWarning)
        EvidenceStore(tmp_path / "evidence.sqlite")
        gc.collect()
    assert not [warning for warning in observed if issubclass(warning.category, ResourceWarning)]


def test_evidence_transactions_close_and_persist_across_reopen(
    tmp_path: Path, connections: Connections,
) -> None:
    """Evidence writes, retrieval events and row results survive explicit connection closure."""
    path = tmp_path / "evidence.sqlite"
    evidence = _evidence("lifetime", "An exact source passage.")
    store = EvidenceStore(path)
    connections.assert_closed()
    reference = store.put(evidence, "corpus-1")
    connections.assert_closed()
    assert store.retrieve(reference.reference_id, "corpus-1") == evidence
    connections.assert_closed()
    assert len(store.history(reference.reference_id)) == 1
    connections.assert_closed()
    reopened = EvidenceStore(path)
    assert reopened.retrieve(reference.reference_id, "corpus-1") == evidence
    assert len(reopened.history(reference.reference_id)) == 2
    connections.assert_closed()


@pytest.mark.parametrize("operation", ["put", "retrieve", "history", "initialize"])
def test_evidence_statement_failures_close_connections(
    tmp_path: Path, connections: Connections, operation: str,
) -> None:
    """Failures in each evidence-store transaction still explicitly close its connection."""
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    reference = store.put(_evidence("error", "Retained evidence."), "corpus-1")
    connections.fail_sql = {
        "put": "INSERT INTO evidence_store",
        "retrieve": "SELECT * FROM evidence_store",
        "history": "SELECT retrieved_at, query",
        "initialize": "CREATE TABLE IF NOT EXISTS evidence_store",
    }[operation]
    with pytest.raises(sqlite3.OperationalError, match="injected statement failure"):
        if operation == "put":
            store.put(_evidence("second", "Another passage."), "corpus-1")
        elif operation == "retrieve":
            store.retrieve(reference.reference_id, "corpus-1")
        elif operation == "history":
            store.history(reference.reference_id)
        else:
            EvidenceStore(store.path)
    connections.assert_closed()


def test_retrieval_event_failure_rolls_back_count_before_closing(
    tmp_path: Path, connections: Connections,
) -> None:
    """An event insert failure must undo the earlier retrieval-count update."""
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    reference = store.put(_evidence("rollback", "Preserved source."), "corpus-1")
    before = _dump(store.path)
    connections.fail_sql = "INSERT INTO evidence_retrieval_events"
    with pytest.raises(sqlite3.OperationalError, match="injected statement failure"):
        store.retrieve(reference.reference_id, "corpus-1")
    connections.assert_closed()
    connections.fail_sql = None
    assert _dump(store.path) == before
    assert store.history(reference.reference_id) == []
    connections.assert_closed()


def test_transaction_exit_failure_still_closes_and_does_not_commit(
    tmp_path: Path, connections: Connections,
) -> None:
    """The outer cleanup runs even when transaction exit cannot finish normally."""
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    before = _dump(store.path)
    connections.fail_exit = True
    with pytest.raises(sqlite3.OperationalError, match="transaction-exit failure"):
        store.put(_evidence("no-commit", "Uncommitted write."), "corpus-1")
    connections.assert_closed()
    connections.fail_exit = False
    assert _dump(store.path) == before
    connections.assert_closed()


def test_build_commit_precedes_closed_vacuum_connection(
    tmp_path: Path, connections: Connections,
) -> None:
    """Rebuild closes its committed write transaction before opening VACUUM."""
    path = _database(tmp_path)
    assert len(connections.opened) == 2
    assert connections.previous_closed_at_open == [True, True]
    connections.assert_closed()
    assert CorpusRepository(path).resolve_entity("CRS 25-7-109") is not None
    connections.assert_closed()


def test_failed_rebuild_rolls_back_previous_rows_and_closes(
    tmp_path: Path, connections: Connections, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure after clearing and repopulating an index retains the prior committed corpus."""
    path = _database(tmp_path)
    before = _dump(path)
    original = index._index_corpus

    def fail_after_insert(connection: sqlite3.Connection, root: Path) -> IndexRun:
        original(connection, root)
        raise RuntimeError("injected index failure")

    monkeypatch.setattr(index, "_index_corpus", fail_after_insert)
    opened_before = len(connections.opened)
    with pytest.raises(RuntimeError, match="injected index failure"):
        index.build_index(tmp_path, path, rebuild=True)
    assert len(connections.opened) == opened_before + 1  # No VACUUM after failed indexing.
    connections.assert_closed()
    assert _dump(path) == before
    connections.assert_closed()


def test_failed_vacuum_closes_both_connections_and_preserves_committed_index(
    tmp_path: Path, connections: Connections,
) -> None:
    """The maintenance failure closes its handle without undoing the already committed build."""
    root = _write_fixture_corpus(tmp_path)
    path = root / "index.sqlite"
    connections.fail_sql = "VACUUM"
    with pytest.raises(sqlite3.OperationalError, match="injected statement failure"):
        index.build_index(root, path, rebuild=True)
    assert len(connections.opened) == 2
    connections.assert_closed()
    connections.fail_sql = None
    assert CorpusRepository(path).resolve_entity("CRS-25-7-109") is not None
    connections.assert_closed()


@pytest.mark.parametrize("operation", [
    "resolve_entity", "search_entities", "list_chunks", "list_relations",
    "list_timeline_events", "list_source_versions", "latest_index_run",
])
def test_repository_reads_close_after_success_and_sql_error(
    tmp_path: Path, connections: Connections, operation: str,
) -> None:
    """Every public repository read closes real connections on return and SQL failure."""
    path = _database(tmp_path)
    repository = CorpusRepository(path)
    method = getattr(repository, operation)
    args = () if operation == "latest_index_run" else ("CRS-25-7-109",)
    assert method(*args)
    connections.assert_closed()
    connections.fail_sql = "SELECT"
    with pytest.raises(sqlite3.OperationalError, match="injected statement failure"):
        method(*args)
    connections.assert_closed()


@pytest.mark.parametrize("query", ["Emission", "promulgate"])
def test_repository_search_early_return_closes_iteration(
    tmp_path: Path, connections: Connections, query: str,
) -> None:
    """A hit limit reached during metadata or chunk iteration leaves no live connection."""
    path = _database(tmp_path)
    result = CorpusRepository(path).search_entities(query, limit=1)
    assert len(result) == 1 and result[0].entity.geode_id == "CRS-25-7-109"
    connections.assert_closed()


@pytest.mark.parametrize("operation", ["query", "gate"])
def test_query_bridge_and_gate_close_on_success_and_failure(
    tmp_path: Path, connections: Connections, operation: str,
) -> None:
    """The query bridge and readiness gate own their independent SQLite handles."""
    path = _database(tmp_path)
    if operation == "query":
        assert query_index(path, "CRS 25-7-109")[0].id == "CRS-25-7-109"
    else:
        assert _check_index_run(path).ready
    connections.assert_closed()
    connections.fail_sql = "SELECT"
    with pytest.raises(sqlite3.OperationalError, match="injected statement failure"):
        if operation == "query":
            query_index(path, "CRS 25-7-109")
        else:
            _check_index_run(path)
    connections.assert_closed()
