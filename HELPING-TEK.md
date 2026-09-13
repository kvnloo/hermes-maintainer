# What actually helps Tek (#108914)

Posted 2026-09-13 as kvnloo: https://github.com/NousResearch/hermes-agent/pull/108914#issuecomment-5649915119

Live head at post **and at the factory re-run:** `d65af42305c4b51227e51aafb17fe7f00ba4de50`. Capture fence / fcntl / clipboard cap / provenance had already landed; remaining hole is still epoch-before-input-dispatch.

Factory re-run (same 10-scanner pass as `d947fc8`, now HEAD-only): **CHANGES REQUIRED**. P1-6 probe RED: approval acquire+release, recording backend, no `_dispatch` patch → `code=human_has_control` **and** `click` landed, `epoch=2`. @smfworks confirmed; **#109508** is the cherry-pick (`_fence()` before `_dispatch`). Do **not** post another origin comment unless asked. The previous review pin `d947fc83` is void.

## Origin comment (posted on `d65af42`)

The lease is the right design. Serve, gateway, and CLI don't share memory, so the generation had to live in the file. You already encoded that in `lease.py`: callers keep `admitted.epoch`, because take-over then hand-back leaves the holder as `agent` and the turn is still the human's.

Third round at `d65af42` used it in the right places: fence after `backend.capture()` before persist/spill/vision, optional `fcntl`, clipboard length cap, browser fence by `features.local`. Those land.

One ordering still skips it.

`handle_computer_use` saves `admitted` at the top, then may wait on approval and backend start. The comment at the call lock says a human may have taken over meanwhile — then it calls `assert_agent_may_act()`, which only asks whether the holder is presently human. `_dispatch` then passes `fence` only to read-only handlers (so delivery kwargs don't leak into input). `click` / `type` never consult epoch until `_fence()` after `_dispatch` returns.

So this is still legal: admit at epoch 0, approval waits, human takes over (1) and hands back (2), re-check sees `agent`, `backend.click` runs, postflight notices `epoch != 0` and returns `human_has_control`. The click already happened. `test_takeover_during_an_admitted_action_discards_its_result` patches `_dispatch`, so it cannot fail this path. Compare `admitted.epoch` immediately before `_dispatch` (or call `_fence()` there), not only after. If it moved, don't start the device op.

That's one missing use of the generation you already have. One test that fails until that compare lands: approval callback does acquire+release, recording backend, do not patch `_dispatch`, assert `backend.calls == []`. Then it's a small patch.

Related: #92524 (Linux+Desktop half only; hosted/dashboard remains — not Closes).

Pinned to `d65af42305c4`. If the head moves, this is void.

## Remaining test (red on `d65af42`; JSON-only is a false green)

Keep `test_takeover_during_an_admitted_action_discards_its_result` (postflight only) and Tek's `test_computer_use_capture_fence.py` (persist/vision). Do **not** rewrite the browser fence test to `commands == []`.

**`test_stale_epoch_after_approval_handoff_never_clicks`** (`tests/tools/test_bot_desktop_lease.py`)

- Approval callback does the full take-over / hand-back (`acquire` then `release`), returns `approve_once`. Recording backend (`click` appends). Do **not** patch `_dispatch`.
- Act: `handle_computer_use({"action": "click", "element": 1})`.
- Assert: `code == human_has_control` **and** `backend.calls == []`.
- Pin: holder-only re-check admits AGENT + new epoch; `_dispatch` passes `fence` only to read-only handlers; `backend.click` runs; outer `_fence()` discards the result.
- Patch: immediately before `_dispatch`, if `get().epoch != admitted.epoch` refuse. Keep the existing postflight compare.
