from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from hermes_maintainer.analysis.root_causes import recurring_mechanisms
from hermes_maintainer.config import load_settings
from hermes_maintainer.db import Database
from hermes_maintainer.graph.store import GraphStore
from hermes_maintainer.optimizer.greedy import solve_greedy


def create_app() -> FastAPI:
    settings = load_settings()
    db = Database(settings.paths.database)
    db.initialize()
    app = FastAPI(title="hermes-maintainer", version="0.1.0")
    static = Path(__file__).parent.parent / "ui" / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    @app.get("/api/health")
    def health():
        latest = db.rows("SELECT * FROM sync_runs ORDER BY id DESC LIMIT 10")
        metrics = db.rows(
            "SELECT metric,value,recorded_at FROM metrics WHERE id IN "
            "(SELECT MAX(id) FROM metrics GROUP BY metric) ORDER BY metric"
        )
        return {"sync_runs": latest, "metrics": metrics}

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
        return db.rows(
            f"SELECT id,kind,number,title,state,author,updated_at,url,labels_json FROM nodes{where} "
            "ORDER BY COALESCE(updated_at,'') DESC LIMIT ?",
            tuple(params + [limit]),
        )

    @app.get("/api/nodes/{node_id:path}")
    def node(node_id: str):
        rows = db.rows("SELECT * FROM nodes WHERE id=?", (node_id,))
        if not rows:
            raise HTTPException(404, "node not found")
        payload = rows[0]
        payload["relations"] = GraphStore(db).neighbors(node_id)
        payload["campaigns"] = db.rows(
            "SELECT c.*,cm.role,cm.confidence FROM campaigns c JOIN campaign_members cm ON c.id=cm.campaign_id WHERE cm.node_id=?",
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

    @app.get("/api/campaigns/{campaign_id:path}")
    def campaign(campaign_id: str):
        rows = db.rows("SELECT * FROM campaigns WHERE id=?", (campaign_id,))
        if not rows:
            raise HTTPException(404, "campaign not found")
        members = db.rows(
            """
            SELECT n.id,n.kind,n.number,n.title,n.state,n.url,n.labels_json,cm.role,cm.confidence
            FROM campaign_members cm JOIN nodes n ON n.id=cm.node_id
            WHERE cm.campaign_id=? ORDER BY n.kind,n.number
            """,
            (campaign_id,),
        )
        return {**rows[0], "members": members}

    @app.get("/api/graph")
    def graph():
        return GraphStore(db).export_json()

    @app.get("/api/root-causes")
    def root_causes():
        return recurring_mechanisms(db)

    @app.get("/api/optimizer/greedy")
    def optimizer(max_atoms: int = Query(30, le=200)):
        return solve_greedy(db, max_atoms=max_atoms)

    return app
