from hermes_maintainer.analysis.campaigns import rebuild_campaigns


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
