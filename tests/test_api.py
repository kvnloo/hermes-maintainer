from fastapi.testclient import TestClient

from hermes_maintainer.analysis.campaigns import rebuild_campaigns
from hermes_maintainer.api.app import create_app


def _seed(db):
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('issue:1','x/y','issue',1,'lock race','open','2026-01-01','[\"P1\",\"needs-repro\"]')"
        )
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('pr:2','x/y','pr',2,'fix A','open','2026-01-02','[\"P0\"]')"
        )
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('pr:3','x/y','pr',3,'fix B','open','2026-01-03','[\"P1\",\"gateway\"]')"
        )
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('pr:4','x/y','pr',4,'old donor','closed','2025-01-01','[]')"
        )
    db.add_relation("pr:2", "issue:1", "fixes", 1, evidence_level="reported")
    db.add_relation("pr:3", "issue:1", "fixes", 1, evidence_level="source_confirmed")
    db.add_relation("pr:3", "pr:2", "supersedes", 0.9, evidence_level="source_confirmed")
    rebuild_campaigns(db)
    db.upsert_node({
        "id": "issue:1", "repo": "x/y", "kind": "issue", "number": 1, "sha": None,
        "title": "lock race", "body": "lock race on session", "state": "open", "author": "a",
        "created_at": None, "updated_at": "2026-01-01", "closed_at": None, "url": None,
        "labels_json": '["P1","needs-repro"]', "base_ref": None, "head_ref": None,
        "base_sha": None, "head_sha": None, "draft": 0, "mergeable": None,
        "changed_files": None, "additions": None, "deletions": None,
        "metadata_json": "{}", "last_seen_run": None,
    })


def test_llms_txt_and_dashboard(db):
    client = TestClient(create_app(database=db))
    page = client.get("/")
    assert page.status_code == 200
    assert "hermes-maintainer" in page.text
    assert 'id="flow"' in page.text
    llms = client.get("/llms.txt")
    assert llms.status_code == 200
    assert llms.text.startswith("# hermes-maintainer")
    assert "xyflow" in llms.text
    assert "read-only" in llms.text.lower()
    assert client.get("/README.md").status_code == 200
    assert client.get("/graph").status_code == 200


def test_campaign_graph_roles_and_filters(db):
    _seed(db)
    client = TestClient(create_app(database=db))
    campaigns = client.get("/api/campaigns").json()
    assert campaigns
    campaign_id = campaigns[0]["id"]
    detail = client.get(f"/api/campaigns/{campaign_id}").json()
    roles = {m["id"]: m["role"] for m in detail["members"]}
    assert roles["issue:1"] == "canonical_problem"
    assert roles["pr:3"] == "survivor"
    assert roles["pr:2"] == "superseded"
    graph = client.get(f"/api/campaigns/{campaign_id}/graph").json()
    assert {n["id"] for n in graph["nodes"]} >= {"issue:1", "pr:2", "pr:3"}
    assert any(rel["relation_type"] == "fixes" for rel in graph["relations"])
    p0 = client.get(f"/api/graph?campaign_id={campaign_id}&priority=p0").json()
    assert {n["id"] for n in p0["nodes"]} == {"pr:2"}
    blocker = client.get(f"/api/graph?campaign_id={campaign_id}&blocker=needs-repro").json()
    assert {n["id"] for n in blocker["nodes"]} == {"issue:1"}
    evidence = client.get(
        f"/api/graph?campaign_id={campaign_id}&evidence_level=source_confirmed"
    ).json()
    assert graph["relations"]
    assert all(rel["evidence_level"] == "source_confirmed" for rel in evidence["relations"])


def test_demo_graph_from_seeds(db):
    client = TestClient(create_app(database=db))
    data = client.get("/api/graph/demo").json()
    assert data["source"] == "seed"
    assert data["nodes"]
    assert data["relations"]
    kinds = {n["kind"] for n in data["nodes"]}
    assert "issue" in kinds and "pr" in kinds
    assert "campaign" in kinds and "file" in kinds and "invariant" in kinds
    family = client.get("/api/graph/demo?family=ci-verdict-integrity").json()
    assert family["campaign"]["id"] == "seed:ci-verdict-integrity"
    architecture = client.get("/api/graph/architecture").json()
    assert {n["id"] for n in architecture["nodes"]} >= {
        "arch:sqlite-backlog",
        "file:graph/store.py",
        "invariant:evidence-before-closure",
    }
    assert architecture["relations"]


def test_search_and_health(db):
    _seed(db)
    client = TestClient(create_app(database=db))
    assert client.get("/api/health").status_code == 200
    hits = client.get("/api/search", params={"q": "lock"}).json()
    assert any(h["id"] == "issue:1" for h in hits)


def test_graph_endpoints_keep_namespaced_ids(db):
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('acme/widgets:issue:9','acme/widgets','issue',9,'lock','open','2026-01-01','[]')"
        )
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('acme/widgets:pr:8','acme/widgets','pr',8,'fix','open','2026-01-02','[]')"
        )
    db.add_relation("acme/widgets:pr:8", "acme/widgets:issue:9", "fixes", 1)
    rebuild_campaigns(db)
    client = TestClient(create_app(database=db))
    graph = client.get("/api/graph?scope=recent").json()
    ids = {n["id"] for n in graph["nodes"]}
    assert "acme/widgets:issue:9" in ids
    assert "acme/widgets:pr:8" in ids
    node = client.get("/api/nodes/acme/widgets:issue:9").json()
    assert node["id"] == "acme/widgets:issue:9"
    assert node["repo"] == "acme/widgets"


def test_graph_export_prefers_connected_family_without_campaigns(db):
    with db.connect() as conn:
        for index in range(1, 21):
            conn.execute(
                "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
                f"VALUES('issue:{index}','x/y','issue',{index},'isolate {index}','open','2026-06-01','[]')"
            )
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('issue:900','x/y','issue',900,'cluster root','open','2026-01-01','[]')"
        )
        conn.execute(
            "INSERT INTO nodes(id,repo,kind,number,title,state,updated_at,labels_json) "
            "VALUES('pr:901','x/y','pr',901,'cluster fix','open','2026-01-01','[]')"
        )
    db.add_relation("pr:901", "issue:900", "fixes", 1)
    client = TestClient(create_app(database=db))
    graph = client.get("/api/graph?scope=recent&limit=10").json()
    ids = {n["id"] for n in graph["nodes"]}
    assert "issue:900" in ids
    assert "pr:901" in ids
    assert any(rel["relation_type"] == "fixes" for rel in graph["relations"])
