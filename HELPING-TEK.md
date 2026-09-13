# What actually helps Tek (#108914)

Posted 2026-09-13 as kvnloo on **VOID** pin `d65af423`: https://github.com/NousResearch/hermes-agent/pull/108914#issuecomment-5649915119

Leftovers (non-blocking) posted on live HEAD `bc36ddb5`: https://github.com/NousResearch/hermes-agent/pull/108914#issuecomment-5650142924

**Live HEAD:** `bc36ddb5f9696c25acc5d51cf29a961710e2d5a3`. Fourth round cherry-picked #109508 (`_fence()` before `_dispatch`). The hole in the first comment is **closed**.

## Leftovers comment (posted on `bc36ddb5`)

The fence before `_dispatch` is in at `bc36ddb5`. That's the missing use of the generation you already had — persist, vision, and the device op now all consult it. #109508 was the right patch.

Three leftovers that aren't a second P1 round:

1. Title still ends `(#92524)`. That issue is hosted cloud-browser. The body already says Related and does not close it; the parenthetical still points at the other product.
2. `bot-screen.md` YAML shows `auto_start: true` while the default is off. `computer-use.md` still says Hermes "starts on first use." The prose one paragraph up ("off by default") is already honest.
3. #109508 / #109505 / #109446 are cherry-picked and dirty against this head. Close them when this lands.

Takeover-doesn't-wait-for-in-flight is your ruling. Fedora nits are already on the receipt.

Pinned to `bc36ddb5f969`. If the head moves, this is void.

Did **not** dump: writer lock, 4000 overlay, in-flight QUIESCING, Fedora Provides nits (coe0718 already re-pinned those).

## Factory re-pin (`bc36ddb5`)

**KEEP.** P1-6 probe green. ChatGPT Layer A (persist-before-epoch, approval-handoff click, fcntl) all landed. Layer B kernel/PII stays off this PR. Remaining: title `(#92524)`, `auto_start` YAML, writer lock, 4000 overlay vs “re-attach.”

## Origin comment (historical — posted on `d65af42`)

The lease is the right design. Serve, gateway, and CLI don't share memory, so the generation had to live in the file. You already encoded that in `lease.py`: callers keep `admitted.epoch`, because take-over then hand-back leaves the holder as `agent` and the turn is still the human's.

Third round at `d65af42` used it in the right places: fence after `backend.capture()` before persist/spill/vision, optional `fcntl`, clipboard length cap, browser fence by `features.local`. Those land.

One ordering still skips it.

`handle_computer_use` saves `admitted` at the top, then may wait on approval and backend start. The comment at the call lock says a human may have taken over meanwhile — then it calls `assert_agent_may_act()`, which only asks whether the holder is presently human. `_dispatch` then passes `fence` only to read-only handlers (so delivery kwargs don't leak into input). `click` / `type` never consult epoch until `_fence()` after `_dispatch` returns.

So this is still legal: admit at epoch 0, approval waits, human takes over (1) and hands back (2), re-check sees `agent`, `backend.click` runs, postflight notices `epoch != 0` and returns `human_has_control`. The click already happened. `test_takeover_during_an_admitted_action_discards_its_result` patches `_dispatch`, so it cannot fail this path. Compare `admitted.epoch` immediately before `_dispatch` (or call `_fence()` there), not only after. If it moved, don't start the device op.

That's one missing use of the generation you already have. One test that fails until that compare lands: approval callback does acquire+release, recording backend, do not patch `_dispatch`, assert `backend.calls == []`. Then it's a small patch.

Related: #92524 (Linux+Desktop half only; hosted/dashboard remains — not Closes).

Pinned to `d65af42305c4`. If the head moves, this is void.

## What landed (round 4)

`tool.py:303` `_fence()` before `_dispatch`. Test `test_takeover_handback_during_approval_does_not_start_the_device_op` green on `bc36ddb5`. Tek credited kvnloo + smfworks; cherry-picked #109508 with authorship.
