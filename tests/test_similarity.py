from hermes_maintainer.analysis.similarity import lexical_similarity


def test_related_bug_reports_score_above_unrelated_pair():
    a = {"title": "OAuth refresh token race clears session", "body": "two processes rotate refresh tokens"}
    b = {"title": "MCP OAuth rotating refresh token race", "body": "peer process replaces the refresh credential"}
    c = {"title": "Desktop sidebar spacing", "body": "padding is too large around home"}
    related, _ = lexical_similarity(a, b)
    unrelated, _ = lexical_similarity(a, c)
    assert related > unrelated
