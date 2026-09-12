# What actually helps Tek

The ChatGPT share is two documents. **99% is Kevin’s kernel/PII/research-loop agenda. 1% is a gift for teknium1 on #108914.**

## The 1%

Tek already built the abstraction: on-disk lease + `epoch`, because serve / gateway / CLI do not share memory. Julien already proved holder-only fails a take-over/hand-back. The remaining bugs are effects that still ignore that generation.

1. Compare `admitted.epoch` **before** `_dispatch` (approval + take-over + hand-back still clicks).
2. Compare it **before** persist / aux-vision (the JSON refuse does not retract a published frame).
3. Isolate `fcntl` so Windows `computer_use` does not import Linux Bot Screen.
4. Cap RFB clipboard length (the filter is not a gate if `_buf` is unbounded).

Show up with **two failing tests + those patches**. Do not show up with a user-space kernel, DisplayTarget, PII middleware, OSWorld, or “I redesigned Hermes.”

`frontier-kb` / `aodl` / `kerdoios` are not in this workspace (Mem0 unauthenticated; no local trees). They were not used.

Ten 3-pass reads are running to confirm this cut and tighten the paste-ready comment.
