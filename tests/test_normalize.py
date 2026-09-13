from hermes_maintainer.github.normalize import explicit_references


def test_explicit_references_preserve_relation_types():
    body = "Fixes #10. Supersedes #11. Related: #12. See https://github.com/x/y/pull/13"
    refs = {(kind, num, repo) for kind, num, _conf, _ev, repo in explicit_references(body, default_repo="a/b")}
    assert ("fixes", 10, "a/b") in refs
    assert ("supersedes", 11, "a/b") in refs
    assert ("related", 12, "a/b") in refs
    assert ("references_pr", 13, "x/y") in refs
