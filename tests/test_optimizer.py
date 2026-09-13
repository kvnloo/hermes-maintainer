from hermes_maintainer.optimizer.greedy import solve_greedy


def test_greedy_prefers_high_coverage_per_cost(db):
    with db.connect() as conn:
        for i in (1, 2, 3):
            conn.execute("INSERT INTO nodes(id,repo,kind,number,title,state) VALUES(?,?,?,?,?,?)", (f"issue:{i}", "x/y", "issue", i, f"i{i}", "open"))
        conn.execute("INSERT INTO nodes(id,repo,kind,number,title,state) VALUES('pr:10','x/y','pr',10,'wide','open')")
        conn.execute("INSERT INTO nodes(id,repo,kind,number,title,state) VALUES('pr:11','x/y','pr',11,'narrow','open')")
        conn.execute("INSERT INTO fix_atoms(id,pr_id,title,cost,value) VALUES('atom:10:pr','pr:10','wide',2,200)")
        conn.execute("INSERT INTO fix_atoms(id,pr_id,title,cost,value) VALUES('atom:11:pr','pr:11','narrow',5,100)")
        conn.execute("INSERT INTO fix_atom_coverage VALUES('atom:10:pr','issue:1','fixes',1)")
        conn.execute("INSERT INTO fix_atom_coverage VALUES('atom:10:pr','issue:2','fixes',1)")
        conn.execute("INSERT INTO fix_atom_coverage VALUES('atom:11:pr','issue:3','fixes',1)")
    result = solve_greedy(db, max_atoms=1)
    assert result["selected"][0]["id"] == "atom:10:pr"
