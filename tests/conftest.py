from __future__ import annotations

from pathlib import Path

import pytest

from hermes_maintainer.db import Database


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "test.db")
    database.initialize()
    return database
