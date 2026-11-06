#!/usr/bin/env python3
"""Maintainer activity for a GitHub repo: who merges and reviews what, and how fast.

Read-only (GraphQL search via `gh`). Writes <out>/maintainers.json and <out>/MAINTAINERS-ACTIVITY.md.
  python3 scripts/maintainer-activity.py --repo NousResearch/hermes-agent --days 30 --out <dir>
Areas are the first path segment (two for tools/, gateway/platforms/, plugins/) of each merged PR's files.
"Response" is the first review or comment by anyone other than the author or a bot.
"""
import argparse
import collections
import datetime as dt
import json
import pathlib
import statistics
import subprocess
import sys

Q = """query($q:String!,$c:String){search(query:$q,type:ISSUE,first:50,after:$c){issueCount pageInfo{hasNextPage endCursor}
nodes{... on PullRequest{number title createdAt mergedAt author{login} mergedBy{login}
files(first:30){nodes{path}} reviews(first:20){nodes{author{login __typename} state submittedAt}}
comments(first:15){nodes{author{login __typename} createdAt}}}}}}"""


def gql(q, cur):
    a = ["gh", "api", "graphql", "-f", f"query={Q}", "-f", f"q={q}"] + (["-f", f"c={cur}"] if cur else [])
    r = None
    for _ in range(3):
        r = subprocess.run(a, capture_output=True, text=True, timeout=180, check=False)
        if r.returncode == 0:
            return json.loads(r.stdout)["data"]["search"]
    sys.exit(f"gh graphql failed: {r.stderr[:300]}")


def fetch(repo, since, until):
    """Merged PRs in [since, until), split by day so no window hits the 1000-result search cap."""
    out, d = [], since
    while d < until:
        q, cur = f"repo:{repo} is:pr is:merged merged:{d.isoformat()}..{d.isoformat()}", None
        while True:
            s = gql(q, cur)
            out += [n for n in s["nodes"] if n]
            if not s["pageInfo"]["hasNextPage"]:
                break
            cur = s["pageInfo"]["endCursor"]
        d += dt.timedelta(days=1)
    return out


def area(p):
    s = p.split("/")
    return "/".join(s[:2]) if s[0] in ("tools", "plugins", "gateway") and len(s) > 2 else s[0]


def ts(x):
    return dt.datetime.fromisoformat(x)


def hours(a, b):
    return round((ts(b) - ts(a)).total_seconds() / 3600, 1)


def med(v):
    return round(statistics.median(v), 1) if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="NousResearch/hermes-agent")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--watch", default="teknium1")
    ap.add_argument("--out", required=True)
    A = ap.parse_args()
    until = dt.date.today() + dt.timedelta(days=1)
    since = until - dt.timedelta(days=A.days)
    prs = fetch(A.repo, since, until)
    bots = set()
    bot = lambda u: (not u) or u.endswith("[bot]") or u in bots
    merger = collections.Counter(); m_area = collections.defaultdict(collections.Counter)
    reviewer = collections.Counter(); r_area = collections.defaultdict(collections.Counter)
    to_merge = collections.defaultdict(list); to_resp = []; first_by = collections.Counter(); self_merge = 0
    watch = {"merged": [], "reviewed": 0, "approved": 0, "changes_requested": 0, "commented_prs": 0}
    for p in prs:   # GitHub Apps (greptile-apps, copilot reviewer) report __typename Bot without a [bot] suffix
        for n in p["reviews"]["nodes"] + p["comments"]["nodes"]:
            if (n.get("author") or {}).get("__typename") == "Bot": bots.add(n["author"]["login"])
    staff = {(p["mergedBy"] or {}).get("login") for p in prs} - {None}
    ext = []
    for p in prs:
        au = (p["author"] or {}).get("login"); mb = (p["mergedBy"] or {}).get("login")
        areas = {area(f["path"]) for f in p["files"]["nodes"]} or {"(none)"}
        if mb:
            merger[mb] += 1; to_merge[mb].append(hours(p["createdAt"], p["mergedAt"]))
            for a in areas: m_area[mb][a] += 1
            self_merge += mb == au
        ev = [(r["submittedAt"], r["author"]["login"], r["state"]) for r in p["reviews"]["nodes"] if r.get("author") and r.get("submittedAt")]
        ev += [(c["createdAt"], c["author"]["login"], "COMMENT") for c in p["comments"]["nodes"] if c.get("author")]
        ev = sorted(e for e in ev if e[1] != au and not bot(e[1]))
        if ev:
            to_resp.append(hours(p["createdAt"], ev[0][0])); first_by[ev[0][1]] += 1
            if au not in staff: ext.append(hours(p["createdAt"], ev[0][0]))
        for u in {e[1] for e in ev if e[2] != "COMMENT"}:
            reviewer[u] += 1
            for a in areas: r_area[u][a] += 1
        w = [e for e in ev if e[1] == A.watch]
        if w:
            watch["reviewed"] += any(e[2] != "COMMENT" for e in w); watch["commented_prs"] += any(e[2] == "COMMENT" for e in w)
            watch["approved"] += any(e[2] == "APPROVED" for e in w); watch["changes_requested"] += any(e[2] == "CHANGES_REQUESTED" for e in w)
        if mb == A.watch:
            watch["merged"].append({"number": p["number"], "title": p["title"][:90], "author": au, "mergedAt": p["mergedAt"], "areas": sorted(areas)[:4]})
    watch["merged"].sort(key=lambda x: x["mergedAt"], reverse=True)
    days = collections.Counter(x["mergedAt"][:10] for x in watch["merged"])
    R = {"repo": A.repo, "window": [since.isoformat(), until.isoformat()], "generated": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
         "merged_prs": len(prs), "self_merged": self_merge,
         "mergers": [{"login": u, "merged": n, "median_hours_open_to_merge": med(to_merge[u]), "top_areas": m_area[u].most_common(6)} for u, n in merger.most_common(15)],
         "reviewers": [{"login": u, "prs_reviewed": n, "top_areas": r_area[u].most_common(6)} for u, n in reviewer.most_common(15)],
         "first_response": {"prs_with_response": len(to_resp), "median_hours": med(to_resp),
                            "p90_hours": round(sorted(to_resp)[int(len(to_resp) * .9)], 1) if to_resp else None,
                            "first_responder": first_by.most_common(10),
                            "external": {"prs": len(ext), "median_hours": med(ext), "p90_hours": round(sorted(ext)[int(len(ext) * .9)], 1) if ext else None}},
         "bots_excluded": sorted(bots),
         "watch": {"login": A.watch, **{k: v for k, v in watch.items() if k != "merged"}, "merged_count": len(watch["merged"]),
                   "merged_per_day": sorted(days.items()), "recent_merges": watch["merged"][:25]}}
    o = pathlib.Path(A.out); o.mkdir(parents=True, exist_ok=True)
    (o / "maintainers.json").write_text(json.dumps(R, indent=1))
    L = [f"# Maintainer activity: {A.repo}, merged PRs {R['window'][0]} to {R['window'][1]}", "",
         f"Generated {R['generated']} by scripts/maintainer-activity.py (read-only GraphQL). {len(prs)} merged PRs; {self_merge} merged by their own author.", "",
         "## Who merges what", "", "| merger | merged | median h open→merge | top areas |", "|---|---:|---:|---|"]
    L += [f"| {m['login']} | {m['merged']} | {m['median_hours_open_to_merge']} | {', '.join(f'{a} ({n})' for a, n in m['top_areas'])} |" for m in R["mergers"]]
    L += ["", "## Who reviews what (approve / request changes / review)", "", "| reviewer | PRs | top areas |", "|---|---:|---|"]
    L += [f"| {r['login']} | {r['prs_reviewed']} | {', '.join(f'{a} ({n})' for a, n in r['top_areas'])} |" for r in R["reviewers"]]
    f = R["first_response"]
    L += ["", "## Response time (merged PRs: first non-author, non-bot review or comment)", "",
          f"- {f['prs_with_response']} of {len(prs)} merged PRs got a human response before or at merge; median {f['median_hours']} h, p90 {f['p90_hours']} h.",
          f"- PRs from non-mergers (outside contributors): {f['external']['prs']} with a response; median {f['external']['median_hours']} h, p90 {f['external']['p90_hours']} h.",
          "- Bots excluded (GitHub Apps): " + ", ".join(R["bots_excluded"][:12]),
          "- First responder most often: " + ", ".join(f"{u} ({n})" for u, n in f["first_responder"]), "",
          "Merged-only sample: PRs that never merged are not in this window, so these times are faster than what an average open PR sees.", "",
          f"## {A.watch}", "", f"- Merged {len(watch['merged'])}; reviewed {watch['reviewed']} (approved {watch['approved']}, changes requested {watch['changes_requested']}); commented on {watch['commented_prs']}.",
          "- Merges per day: " + ", ".join(f"{d[5:]} {n}" for d, n in sorted(days.items())), "", "| PR | author | merged | areas | title |", "|---|---|---|---|---|"]
    L += [f"| [#{m['number']}](https://github.com/{A.repo}/pull/{m['number']}) | {m['author']} | {m['mergedAt'][:16]} | {', '.join(m['areas'])} | {m['title']} |" for m in watch["merged"][:25]]
    (o / "MAINTAINERS-ACTIVITY.md").write_text("\n".join(L) + "\n")
    print(json.dumps({"merged_prs": len(prs), "mergers": merger.most_common(5), "watch_merged": len(watch["merged"]), "median_resp_h": f["median_hours"]}))


if __name__ == "__main__":
    main()
