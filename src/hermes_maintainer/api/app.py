from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from hermes_maintainer.analysis.root_causes import recurring_mechanisms
from hermes_maintainer.config import load_settings
from hermes_maintainer.db import Database
from hermes_maintainer.graph.demo import seed_campaign_graph
from hermes_maintainer.graph.store import GraphStore, fts_query, parse_labels
from hermes_maintainer.optimizer.greedy import solve_greedy


def create_app(database: Database | None = None) -> FastAPI:
    settings = load_settings()
    db = database if database is not None else Database(settings.paths.database)
    db.initialize()
    graph = GraphStore(db)
    app = FastAPI(title="hermes-maintainer", version="0.1.0")
    static = Path(__file__).parent.parent / "ui" / "static"
    docs_dir = settings.root / "docs"
    app.mount("/static", StaticFiles(directory=static), name="static")
    if docs_dir.is_dir():
        app.mount("/docs", StaticFiles(directory=docs_dir), name="docs")

    def _index():
        response = FileResponse(static / "index.html")
        response.headers["Link"] = '</llms.txt>; rel="describedby"'
        return response

    @app.middleware("http")
    async def describedby(_request, call_next):
        response: Response = await call_next(_request)
        if "link" not in response.headers:
            response.headers["Link"] = '</llms.txt>; rel="describedby"'
        return response

    @app.get("/")
    def index():
        return _index()

    @app.get("/graph")
    def graph_page():
        return _index()

    @app.get("/llms.txt")
    def llms_txt():
        path = settings.root / "llms.txt"
        if not path.is_file():
            raise HTTPException(404, "llms.txt not found")
        return FileResponse(path, media_type="text/markdown; charset=utf-8")

    @app.get("/README.md")
    def readme():
        path = settings.root / "README.md"
        if not path.is_file():
            raise HTTPException(404, "README.md not found")
        return FileResponse(path, media_type="text/markdown; charset=utf-8")

    @app.get("/api/health")
    def health():
        latest = db.rows("SELECT * FROM sync_runs ORDER BY id DESC LIMIT 10")
        metrics = db.rows(
            "SELECT metric,value,recorded_at FROM metrics WHERE id IN "
            "(SELECT MAX(id) FROM metrics GROUP BY metric) ORDER BY metric"
        )
        return {"sync_runs": latest, "metrics": metrics}

    @app.get("/api/filters")
    def filters():
        return graph.filter_catalog()

    @app.get("/api/search")
    def search(q: str = Query("", min_length=0), limit: int = Query(40, le=200)):
        if not q.strip():
            return []
        try:
            hits = db.rows(
                "SELECT node_id FROM backlog_fts WHERE backlog_fts MATCH ? LIMIT ?",
                (fts_query(q), limit),
            )
        except sqlite3.OperationalError:
            return []
        ids = [row["node_id"] for row in hits]
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = db.rows(
            f"SELECT id,kind,number,title,state,author,updated_at,url,labels_json FROM nodes "
            f"WHERE id IN ({placeholders})",
            tuple(ids),
        )
        for row in rows:
            row["labels"] = parse_labels(row.pop("labels_json", "[]"))
        return rows

    @app.get("/api/nodes")
    def nodes(
        kind: str | None = None,
        state: str | None = "open",
        limit: int = Query(200, le=2000),
    ):
        clauses, params = [], []
        if kind:
            clauses.append("kind=?")
            params.append(kind)
        if state:
            clauses.append("state=?")
            params.append(state)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = db.rows(
            f"SELECT id,kind,number,title,state,author,updated_at,url,labels_json FROM nodes{where} "
            "ORDER BY COALESCE(updated_at,'') DESC LIMIT ?",
            tuple(params + [limit]),
        )
        for row in rows:
            row["labels"] = parse_labels(row.pop("labels_json", "[]"))
        return rows

    @app.get("/api/nodes/{node_id:path}")
    def node(node_id: str):
        rows = db.rows("SELECT * FROM nodes WHERE id=?", (node_id,))
        if not rows:
            raise HTTPException(404, "node not found")
        payload = rows[0]
        payload["labels"] = parse_labels(payload.pop("labels_json", "[]"))
        payload["metadata"] = json.loads(payload.pop("metadata_json") or "{}")
        payload["relations"] = graph.neighbors(node_id)
        payload["campaigns"] = db.rows(
            "SELECT c.*,cm.role,cm.confidence FROM campaigns c JOIN campaign_members cm "
            "ON c.id=cm.campaign_id WHERE cm.node_id=?",
            (node_id,),
        )
        return payload

    @app.get("/api/campaigns")
    def campaigns(limit: int = Query(200, le=1000)):
        return db.rows(
            """
            SELECT c.*,COUNT(cm.node_id) member_count
            FROM campaigns c LEFT JOIN campaign_members cm ON c.id=cm.campaign_id
            GROUP BY c.id ORDER BY c.score DESC, member_count DESC LIMIT ?
            """,
            (limit,),
        )

    @app.get("/api/campaigns/{campaign_id}/graph")
    def campaign_graph(
        campaign_id: str,
        kind: str | None = None,
        state: str | None = None,
        priority: str | None = None,
        component: str | None = None,
        blocker: str | None = None,
        updated_within_days: int | None = Query(None, ge=1, le=3650),
        stale_days: int | None = Query(None, ge=1, le=3650),
        evidence_level: str | None = None,
        q: str | None = None,
        limit: int = Query(250, le=2000),
    ):
        payload = graph.export_subgraph(
            campaign_id=campaign_id,
            kind=kind,
            state=state,
            priority=priority,
            component=component,
            blocker=blocker,
            updated_within_days=updated_within_days,
            stale_days=stale_days,
            evidence_level=evidence_level,
            q=q,
            limit=limit,
        )
        if payload["campaign"] is None:
            raise HTTPException(404, "campaign not found")
        return payload

    @app.get("/api/campaigns/{campaign_id}")
    def campaign(campaign_id: str):
        rows = db.rows("SELECT * FROM campaigns WHERE id=?", (campaign_id,))
        if not rows:
            raise HTTPException(404, "campaign not found")
        members = db.rows(
            """
            SELECT n.id,n.kind,n.number,n.title,n.state,n.url,n.labels_json,n.updated_at,
                   n.author,cm.role,cm.confidence
            FROM campaign_members cm JOIN nodes n ON n.id=cm.node_id
            WHERE cm.campaign_id=? ORDER BY n.kind,n.number
            """,
            (campaign_id,),
        )
        for member in members:
            member["labels"] = parse_labels(member.pop("labels_json", "[]"))
        relations = graph.relations_among(member["id"] for member in members)
        return {**rows[0], "members": members, "relations": relations}

    @app.get("/api/graph/demo")
    def demo_graph(family: str | None = None):
        return seed_campaign_graph(settings.root, family)

    @app.get("/api/graph")
    def graph_export(
        campaign_id: str | None = None,
        kind: str | None = None,
        state: str | None = None,
        priority: str | None = None,
        component: str | None = None,
        blocker: str | None = None,
        updated_within_days: int | None = Query(None, ge=1, le=3650),
        stale_days: int | None = Query(None, ge=1, le=3650),
        evidence_level: str | None = None,
        q: str | None = None,
        scope: str = "campaign",
        limit: int = Query(250, le=2000),
    ):
        return graph.export_subgraph(
            campaign_id=campaign_id,
            kind=kind,
            state=state,
            priority=priority,
            component=component,
            blocker=blocker,
            updated_within_days=updated_within_days,
            stale_days=stale_days,
            evidence_level=evidence_level,
            q=q,
            scope=scope,
            limit=limit,
        )

    @app.get("/api/root-causes")
    def root_causes():
        return recurring_mechanisms(db)

    @app.get("/api/optimizer/greedy")
    def optimizer(max_atoms: int = Query(30, le=200)):
        return solve_greedy(db, max_atoms=max_atoms)

    return app
