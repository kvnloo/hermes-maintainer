from __future__ import annotations

from hermes_maintainer.db import Database
from hermes_maintainer.github.ids import node_kind
from hermes_maintainer.optimizer.greedy import load_atoms


def solve_cpsat(db: Database, max_atoms: int = 50) -> dict:
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise RuntimeError("Install hermes-maintainer[solver] to use CP-SAT") from exc

    atoms = load_atoms(db)
    model = cp_model.CpModel()
    x = {a.id: model.new_bool_var(a.id.replace(":", "_")) for a in atoms}
    model.add(sum(x.values()) <= max_atoms)

    coverage_to_atoms: dict[str, list] = {}
    for atom in atoms:
        for target in atom.covers | atom.supersedes:
            coverage_to_atoms.setdefault(target, []).append(atom)

    y = {target: model.new_bool_var("covered_" + target.replace(":", "_")) for target in coverage_to_atoms}
    for target, candidates in coverage_to_atoms.items():
        model.add(y[target] <= sum(x[a.id] for a in candidates))

    # Integer scaling keeps CP-SAT exact.
    objective_terms = []
    for atom in atoms:
        objective_terms.append(int(atom.value * 100) * x[atom.id])
        objective_terms.append(-int(atom.cost * 25) * x[atom.id])
    for target, var in y.items():
        objective_terms.append((10000 if node_kind(target) == "issue" else 1200) * var)
    model.maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.solve(model)
    selected = [a for a in atoms if solver.value(x[a.id])]
    return {
        "status": solver.status_name(status),
        "selected": [a.id for a in selected],
        "covered": sorted(t for t, var in y.items() if solver.value(var)),
        "objective": solver.objective_value,
    }
