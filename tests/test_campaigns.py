from hermes_maintainer.analysis.campaigns import assign_member_roles, rebuild_campaigns


def test_campaign_groups_issue_and_competing_prs(db):
    with db.connect() as conn:
        conn.execute("INSERT INTO nodes(id,repo,kind,number,title,state,updated_at) VALUES('issue:1','x/y','issue',1,'bug','open','2026-01-01')")
        conn.execute("INSERT INTO nodes(id,repo,kind,number,title,state,updated_at) VALUES('pr:2','x/y','pr',2,'fix A','open','2026-01-02')")
        conn.execute("INSERT INTO nodes(id,repo,kind,number,title,state,updated_at) VALUES('pr:3','x/y','pr',3,'fix B','open','2026-01-03')")
    db.add_relation("pr:2", "issue:1", "fixes", 1)
    db.add_relation("pr:3", "issue:1", "fixes", 1)
    result = rebuild_campaigns(db)
    assert result["campaigns"] == 1
    assert result["members"] == 3
    roles = {r["node_id"]: r["role"] for r in db.rows("SELECT node_id, role FROM campaign_members")}
    assert roles["issue:1"] == "canonical_problem"
    assert roles["pr:3"] == "survivor"
    assert roles["pr:2"] == "active_implementation"


def test_assign_member_roles_survivor_donor_provenance():
    members = [
        {"id": "issue:1", "kind": "issue", "state": "open", "updated_at": "1"},
        {"id": "pr:2", "kind": "pr", "state": "open", "updated_at": "2"},
        {"id": "pr:3", "kind": "pr", "state": "closed", "updated_at": "3"},
        {"id": "pr:4", "kind": "pr", "state": "open", "updated_at": "4"},
    ]
    relations = [
        {"src_id": "pr:2", "dst_id": "issue:1", "relation_type": "fixes"},
        {"src_id": "pr:4", "dst_id": "pr:2", "relation_type": "supersedes"},
        {"src_id": "pr:3", "dst_id": "pr:2", "relation_type": "incorporates_commit"},
    ]
    roles = assign_member_roles(members, relations, "pr:4")
    assert roles["issue:1"] == "canonical_problem"
    assert roles["pr:4"] == "survivor"
    assert roles["pr:2"] == "superseded"
    assert roles["pr:3"] == "provenance"
