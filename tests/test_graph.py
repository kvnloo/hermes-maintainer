from hermes_maintainer.graph.store import GraphStore


def _node(db, node_id, kind):
    db.upsert_node({
        "id": node_id, "repo": "x/y", "kind": kind, "number": int(node_id.split(':')[1]),
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
