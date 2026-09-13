from hermes_maintainer.github.normalize import explicit_references


def test_explicit_references_preserve_relation_types():
    body = "Fixes #10. Supersedes #11. Related: #12. See https://github.com/x/y/pull/13"
    refs = {(kind, num) for kind, num, *_ in explicit_references(body)}
    assert ("fixes", 10) in refs
    assert ("supersedes", 11) in refs
    assert ("related", 12) in refs
    assert ("references_pr", 13) in refs
