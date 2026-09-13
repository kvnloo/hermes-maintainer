from __future__ import annotations

import contextlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator


class Database:
    def __init__(self, path: Path):
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self.connect() as conn:
            conn.executescript(schema)

    @contextlib.contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return None if row is None else row[0]

    def rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def upsert_node(self, payload: dict[str, Any]) -> None:
        columns = [
            "id", "repo", "kind", "number", "sha", "title", "body", "state", "author",
            "created_at", "updated_at", "closed_at", "url", "labels_json", "base_ref",
            "head_ref", "base_sha", "head_sha", "draft", "mergeable", "changed_files",
            "additions", "deletions", "metadata_json", "last_seen_run",
        ]
        values = [payload.get(c) for c in columns]
        assignments = ", ".join(f"{c}=excluded.{c}" for c in columns if c != "id")
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO nodes ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                values,
            )
            if payload.get("kind") in {"issue", "pr"}:
                conn.execute("DELETE FROM backlog_fts WHERE node_id=?", (payload["id"],))
                conn.execute(
                    "INSERT INTO backlog_fts(node_id,title,body,labels) VALUES(?,?,?,?)",
                    (
                        payload["id"],
                        payload.get("title") or "",
                        payload.get("body") or "",
                        " ".join(json.loads(payload.get("labels_json") or "[]")),
                    ),
                )

    def add_relation(
        self,
        src_id: str,
        dst_id: str,
        relation_type: str,
        confidence: float = 1.0,
        evidence_level: str = "reported",
        evidence: str | None = None,
        source: str = "deterministic",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO relations(src_id,dst_id,relation_type,confidence,evidence_level,evidence,source)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(src_id,dst_id,relation_type) DO UPDATE SET
                  confidence=excluded.confidence,
                  evidence_level=excluded.evidence_level,
                  evidence=excluded.evidence,
                  source=excluded.source,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (src_id, dst_id, relation_type, confidence, evidence_level, evidence, source),
            )
