from hermes_maintainer.graph.store import GraphStore


def _node(db, node_id, kind, repo="x/y"):
    number = int(str(node_id).rsplit(":", 1)[-1])
    db.upsert_node({
        "id": node_id, "repo": repo, "kind": kind, "number": number,
        "sha": None, "title": node_id, "body": "", "state": "open", "author": "a",
        "created_at": None, "updated_at": None, "closed_at": None, "url": None,
        "labels_json": "[]", "base_ref": None, "head_ref": None, "base_sha": None,
        "head_sha": None, "draft": 0, "mergeable": None, "changed_files": None,
        "additions": None, "deletions": None, "metadata_json": "{}", "last_seen_run": None,
    })


def test_connected_components_follow_strong_edges(db):
    _node(db, "issue:1", "issue")
    _node(db, "pr:2", "pr")
    _node(db, "issue:3", "issue")
    db.add_relation("pr:2", "issue:1", "fixes", 1.0)
    comps = GraphStore(db).connected_components({"issue:1", "pr:2", "issue:3"})
    assert {"issue:1", "pr:2"} in comps
    assert {"issue:3"} in comps


def test_export_subgraph_caps_and_filters(db):
    _node(db, "issue:1", "issue")
    _node(db, "pr:2", "pr")
    db.add_relation("pr:2", "issue:1", "fixes", 1.0, evidence_level="reported")
    payload = GraphStore(db).export_subgraph(scope="recent", limit=10)
    ids = {n["id"] for n in payload["nodes"]}
    assert "issue:1" in ids
    assert "pr:2" in ids
    assert payload["relations"]


def test_export_subgraph_preserves_namespaced_repo_ids(db):
    _node(db, "acme/widgets:issue:1", "issue", repo="acme/widgets")
    _node(db, "acme/widgets:pr:2", "pr", repo="acme/widgets")
    db.add_relation("acme/widgets:pr:2", "acme/widgets:issue:1", "fixes", 1.0)
    payload = GraphStore(db).export_subgraph(scope="recent", limit=10)
    ids = {n["id"] for n in payload["nodes"]}
    assert ids >= {"acme/widgets:issue:1", "acme/widgets:pr:2"}
    assert all(n["repo"] == "acme/widgets" for n in payload["nodes"])
    assert payload["relations"][0]["src_id"] == "acme/widgets:pr:2"
