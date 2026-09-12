# What actually helps Tek (#108914 @ `d947fc83`)

Gift: two races, two tests, one comment. Linear HITL is the approval gate; GitHub stays quiet until Kevin says post.

`frontier-kb` / `aodl` / `kerdoios` were not in this workspace. Unused.

## Cut (do not say on origin)

User-space kernel, PII/Presidio/#102922, vault/#107704, credential handles/#107700, DisplayTarget/#108878, PER-1430, OSWorld, Playwright recipes, CaMeL/TACIT, competing-PR tables, “I redesigned Hermes,” rediscovering the lease he already wrote, philosophizing that generations cannot cancel in-flight input.

## Inevitable claim (his docstring)

Authority lives on disk because serve, gateway, CLI, and workers do not share memory. `epoch` increments on every transition so an admitted action can tell control changed. Callers already keep that number. The leftover bugs are effects that still ignore it.

Generation numbers do **not** cancel an in-flight click. Epoch-before-dispatch is so the *old* click never starts. In-flight is a separate honesty problem; do not pitch QUIESCING as this week’s PR.

## Paste-ready comment (not posted)

The lease is the right design. Serve, gateway, and CLI don't share memory, so the generation had to live in the file. You already encoded that in `lease.py`: callers keep `admitted.epoch`, because take-over then hand-back leaves the holder as `agent` and the turn is still the human's.

I found two orderings on `d947fc8` that still skip it.

`handle_computer_use` saves `admitted` at the top, then may wait on approval and backend start. The comment at the call lock says a human may have taken over meanwhile — then it calls `assert_agent_may_act()`, which only asks whether the holder is presently human. So this is legal: admit at epoch 0, approval waits, human takes over (1) and hands back (2), re-check sees `agent`, `_dispatch` runs the old click, postflight notices `epoch != 0` and returns `human_has_control`. The click already happened. `test_takeover_during_an_admitted_action_discards_its_result` patches `_dispatch`, so it cannot fail this path. Compare `admitted.epoch` immediately before `_dispatch`, not only after. If it moved, don't start the device op.

Persist and aux-vision run inside `_dispatch`. The outer epoch refuse cannot retract a file on disk or a frame already sent to vision. Check generation before persist/vision; keep the outer refuse.

That's one missing use of the generation you already have. Two tests that fail until those compares land; then it's a small patch.

Two nits to land with those tests: lazy-import `fcntl` off the Windows CU path, and cap ClientCutText on `_buf` (`MAX_PAYLOAD=1_048_576` is enough). Your `--session` fence already uses generation; real-profile Chromium is CDP on that DISPLAY and `_shares_bot_desktop_browser` treats any `cdp_url` as remote — fence by local launch provenance, keep the cloud/user-CDP exemption.

Related: #92524 (Linux+Desktop half only; hosted/dashboard remains — not Closes).

Pinned to `d947fc83`. If the head moves, this is void.

## Two tests (red on this pin; JSON-only is a false green)

Keep `test_takeover_during_an_admitted_action_discards_its_result`. It is postflight only. Do **not** rewrite the browser fence test to `commands == []` (in-flight spawn is not what generation numbers cancel).

Do **not** `setattr(..., "_dispatch", ...)`. A fake `_dispatch` hides persist/aux-vision and the pre-dispatch holder-only gap. Spy by wrapping and calling through, or by a recording backend that real `_dispatch` invokes.

**1. `test_stale_epoch_after_approval_handoff_never_clicks`** (`tests/tools/test_bot_desktop_lease.py`)

- Approval callback does the full take-over / hand-back (`acquire` then `release`), returns `approve_once`. Recording backend (`click` appends). Do **not** patch `_dispatch`. Do not flip the lease inside `_get_backend` or `backend.click`.
- Act: `handle_computer_use({"action": "click", "element": 1})`.
- Assert: `code == human_has_control` **and** `backend.calls == []`. JSON-only is already green on this pin.
- Pin: holder-only re-check at `tool.py:284-287` admits AGENT + new epoch; `_dispatch` clicks; `:291` discards the result.
- Patch: immediately before `_dispatch`, if `get().epoch != admitted.epoch` refuse. Keep the existing postflight compare.

**2. `test_capture_takeover_does_not_persist_or_route_aux_vision`**

- Do **not** patch `_dispatch`. Backend `capture()` does acquire+release then returns a persistable 8×8 PNG (smaller skips persist as `too_small`). Force `_should_route_through_aux_vision` True or the vision assert is a false green.
- Wrap `_persist_capture_image` and `_route_capture_through_aux_vision` **and call through**. Replacing persist with a no-op hides the leak.
- Assert: `human_has_control` **and** `persist_calls == []` and `vision_calls == []`. Optional: no `computer_use_*.*` under redirected cache.
- Pin: `_dispatch` still publishes, then `:291` refuses the envelope.
- Patch: after `backend.capture()`, before `_persist_capture_image` / `_route_capture_through_aux_vision`. Same number covers `capture_after` via `_maybe_follow_capture`.
