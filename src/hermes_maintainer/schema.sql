PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mode TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  git_sha TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('issue','pr','commit','file','campaign','fix_atom')),
  number INTEGER,
  sha TEXT,
  title TEXT,
  body TEXT,
  state TEXT,
  author TEXT,
  created_at TEXT,
  updated_at TEXT,
  closed_at TEXT,
  url TEXT,
  labels_json TEXT NOT NULL DEFAULT '[]',
  base_ref TEXT,
  head_ref TEXT,
  base_sha TEXT,
  head_sha TEXT,
  draft INTEGER NOT NULL DEFAULT 0,
  mergeable TEXT,
  changed_files INTEGER,
  additions INTEGER,
  deletions INTEGER,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  last_seen_run INTEGER,
  FOREIGN KEY(last_seen_run) REFERENCES sync_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_nodes_kind_state ON nodes(kind, state);
CREATE INDEX IF NOT EXISTS idx_nodes_number ON nodes(kind, number);
CREATE INDEX IF NOT EXISTS idx_nodes_updated ON nodes(updated_at);
CREATE INDEX IF NOT EXISTS idx_nodes_repo ON nodes(repo);

CREATE VIRTUAL TABLE IF NOT EXISTS backlog_fts USING fts5(
  node_id UNINDEXED,
  title,
  body,
  labels,
  tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS relations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_id TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  evidence_level TEXT NOT NULL DEFAULT 'reported',
  evidence TEXT,
  source TEXT NOT NULL DEFAULT 'deterministic',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(src_id, dst_id, relation_type),
  FOREIGN KEY(src_id) REFERENCES nodes(id) ON DELETE CASCADE,
  FOREIGN KEY(dst_id) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rel_src ON relations(src_id);
CREATE INDEX IF NOT EXISTS idx_rel_dst ON relations(dst_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON relations(relation_type);

CREATE TABLE IF NOT EXISTS pr_files (
  pr_id TEXT NOT NULL,
  path TEXT NOT NULL,
  status TEXT,
  additions INTEGER NOT NULL DEFAULT 0,
  deletions INTEGER NOT NULL DEFAULT 0,
  changes INTEGER NOT NULL DEFAULT 0,
  patch_sha256 TEXT,
  PRIMARY KEY(pr_id, path),
  FOREIGN KEY(pr_id) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pr_commits (
  pr_id TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  message TEXT,
  patch_id TEXT,
  PRIMARY KEY(pr_id, commit_sha),
  FOREIGN KEY(pr_id) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  level TEXT NOT NULL,
  status TEXT NOT NULL,
  source_url TEXT,
  source_sha TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(subject_id, evidence_type, source_url, source_sha)
);

CREATE INDEX IF NOT EXISTS idx_evidence_subject ON evidence(subject_id);

CREATE TABLE IF NOT EXISTS campaigns (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'candidate',
  canonical_node_id TEXT,
  score REAL NOT NULL DEFAULT 0,
  summary TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaign_members (
  campaign_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  confidence REAL NOT NULL DEFAULT 0.5,
  PRIMARY KEY(campaign_id, node_id),
  FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
  FOREIGN KEY(node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fix_atoms (
  id TEXT PRIMARY KEY,
  pr_id TEXT,
  title TEXT NOT NULL,
  scope TEXT NOT NULL DEFAULT 'pr',
  status TEXT NOT NULL DEFAULT 'candidate',
  cost REAL NOT NULL DEFAULT 0,
  value REAL NOT NULL DEFAULT 0,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(pr_id) REFERENCES nodes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS fix_atom_coverage (
  atom_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  coverage_type TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY(atom_id, node_id, coverage_type),
  FOREIGN KEY(atom_id) REFERENCES fix_atoms(id) ON DELETE CASCADE,
  FOREIGN KEY(node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  metric TEXT NOT NULL,
  value REAL NOT NULL,
  dimensions_json TEXT NOT NULL DEFAULT '{}'
);
