# Hermes triage audit bundle

Live pins (re-GET 2026-09-13): HERMES_LIVE_PINS.md and LIVE_PINS.json. HERMES_TRIAGE_AUDIT.md still pins historical `205645ee` — do not treat it as current HEAD.

The included campaign seeds are hand-curated and incomplete. All candidates require renewed exact-head validation before landing. The local test results cover isolated audit probes only.

Run the optional checks with Python 3.10+ and PyYAML available:

```bash
python offline_probes.py
```

See scan_coverage.json for limitations and sources.json for pinned primary sources.
