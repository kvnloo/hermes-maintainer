from __future__ import annotations

from dataclasses import asdict

from hermes_maintainer.db import Database
from hermes_maintainer.models import FixAtom


def load_atoms(db: Database) -> list[FixAtom]:
    rows = db.rows("SELECT id,pr_id,title,cost,value FROM fix_atoms WHERE status='candidate'")
    atoms: list[FixAtom] = []
    for row in rows:
        coverage = db.rows(
            "SELECT node_id,coverage_type FROM fix_atom_coverage WHERE atom_id=?",
            (row["id"],),
        )
        atoms.append(
            FixAtom(
                id=row["id"],
                pr_id=row.get("pr_id"),
                title=row["title"],
                cost=float(row["cost"]),
                value=float(row["value"]),
                covers={c["node_id"] for c in coverage if c["coverage_type"] == "fixes"},
                supersedes={c["node_id"] for c in coverage if c["coverage_type"] == "supersedes"},
            )
        )
    return atoms


def solve_greedy(db: Database, max_atoms: int = 50) -> dict:
    remaining = load_atoms(db)
    selected: list[FixAtom] = []
    covered: set[str] = set()
    superseded: set[str] = set()

    while remaining and len(selected) < max_atoms:
        best = None
        best_score = 0.0
        for atom in remaining:
            new_coverage = atom.covers - covered
            new_superseded = atom.supersedes - superseded
            if not new_coverage and not new_superseded:
                continue
            marginal = atom.value
            # Discount value already represented by prior selections.
            if atom.covers:
                marginal *= len(new_coverage) / len(atom.covers)
            if atom.supersedes and not new_superseded:
                marginal *= 0.85
            score = marginal / max(0.01, atom.cost)
            if score > best_score:
                best, best_score = atom, score
        if best is None:
            break
        selected.append(best)
        covered |= best.covers
        superseded |= best.supersedes
        remaining = [a for a in remaining if a.id != best.id]

    return {
        "selected": [
            {
                **asdict(atom),
                "covers": sorted(atom.covers),
                "supersedes": sorted(atom.supersedes),
                "marginal_ratio": atom.value / max(atom.cost, 0.01),
            }
            for atom in selected
        ],
        "covered_issues": sorted(covered),
        "superseded_prs": sorted(superseded),
        "count": len(selected),
    }
