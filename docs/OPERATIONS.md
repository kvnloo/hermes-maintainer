# Operations

## Local workstation

```bash
hermes-maintainer init
hermes-maintainer scan --mode deep
hermes-maintainer analyze
hermes-maintainer serve
```

## Long-running local service

Run two processes under your preferred supervisor:

```bash
hermes-maintainer daemon
hermes-maintainer serve --host 127.0.0.1 --port 8766
```

The database uses WAL locally. Keep the data directory on a local filesystem. If this moves to a
shared/network filesystem, revisit SQLite locking and journal-mode assumptions first.

## Suggested scan cadence

- fast scan: 15 minutes;
- deep enrichment: 6 hours;
- historical backfill: low-priority nightly batch;
- full campaign revalidation: after meaningful `main` advancement or survivor-head movement.

## Backup

The `.data` directory is disposable because the primary sources are GitHub and git. Back up only
if you want to retain historical metric snapshots or agent evidence that has not been published
elsewhere.

## Failure posture

A failed scan must not erase prior graph state. A failed verification must be recorded as unknown
or failed evidence, not converted into a repository action.
