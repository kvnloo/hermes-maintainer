# What actually helps Tek (#108914)

**Live HEAD:** `bc36ddb5f9696c25acc5d51cf29a961710e2d5a3`. Fourth round cherry-picked #109508 (`_fence()` before `_dispatch`). The hole in the first comment is **closed**.

## Consolidation (posted on `bc36ddb5`)

https://github.com/NousResearch/hermes-agent/pull/108914#issuecomment-5650222729

Independent last pass of every named review/inline/issue comment against live head. Mapped Julien's original contract and every later reviewer to landed / skip / leftover. Re-raised six thread items that were never closed (4000 copy vs overlay, install `session_id` not sent from the card, SIGKILL-only install timeout, `/tmp` alloc lock path, no viewer cap, xauth cookie on argv). Did **not** remint landed P1s, in-flight wait, Layer B, or writer lock.

## Leftovers comment (posted on `bc36ddb5`)

https://github.com/NousResearch/hermes-agent/pull/108914#issuecomment-5650142924

The fence before `_dispatch` is in at `bc36ddb5`. That's the missing use of the generation you already had — persist, vision, and the device op now all consult it. #109508 was the right patch.

Three leftovers that aren't a second P1 round:

1. Title still ends `(#92524)`. That issue is hosted cloud-browser. The body already says Related and does not close it; the parenthetical still points at the other product.
2. `bot-screen.md` YAML shows `auto_start: true` while the default is off. `computer-use.md` still says Hermes "starts on first use." The prose one paragraph up ("off by default") is already honest.
3. #109508 / #109505 / #109446 are cherry-picked and dirty against this head. Close them when this lands.

Takeover-doesn't-wait-for-in-flight is your ruling. Fedora nits are already on the receipt.

Pinned to `bc36ddb5f969`. If the head moves, this is void.

## Origin comment (historical — posted on VOID `d65af42`)

https://github.com/NousResearch/hermes-agent/pull/108914#issuecomment-5649915119

The lease is the right design. Serve, gateway, and CLI don't share memory, so the generation had to live in the file. You already encoded that in `lease.py`: callers keep `admitted.epoch`, because take-over then hand-back leaves the holder as `agent` and the turn is still the human's.

Third round at `d65af42` used it in the right places: fence after `backend.capture()` before persist/spill/vision, optional `fcntl`, clipboard length cap, browser fence by `features.local`. Those land.

One ordering still skips it. (`_fence()` before `_dispatch` — now landed on `bc36ddb5`.)

Related: #92524 (Linux+Desktop half only; hosted/dashboard remains — not Closes).

Pinned to `d65af42305c4`. If the head moves, this is void.

## What landed (round 4)

`tool.py:303` `_fence()` before `_dispatch`. Test `test_takeover_handback_during_approval_does_not_start_the_device_op` green on `bc36ddb5`. Tek credited kvnloo + smfworks; cherry-picked #109508 with authorship.
