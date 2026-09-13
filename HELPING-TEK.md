# What actually helps Tek (#108914)

Board hygiene (2026-09-13): `BACKLOG-CLOSE.md`. kvnloo cannot triage. Closed our own duplicate #102262. The ~2,750-item play is `label:duplicate` + obvious `invalid` — already classified, still open. See that file for maintainer commands.

## Live GET 2026-09-13T13:32Z

No newer **teknium1** PR for headed cloud / DisplayTarget / WebVNC / cloud-computer-control through CUA. Open CUA-desktop product remains [#108914](https://github.com/NousResearch/hermes-agent/pull/108914) @ `77123c0ef3e1c24d6712a37720e912f3fc68d9b3`. Prior pin `bc36ddb5` is **void**.

HEAD moved: leftover pass Tek promised at 12:37 **is in tree** (4000 re-attach, install `session_id`, SIGTERM, `_ALLOC_LOCK` out of `/tmp`, xauth via stdin, honest `auto_start` docs) **plus** `Merge origin/main`, so [#109649](https://github.com/NousResearch/hermes-agent/pull/109649) fail-closed CU gate sits next to the lease fence. Do not remint those. Do not remint landed fence comments.

Hero “Last seen” has vitest. Docs YAML `auto_start: false`. Remaining claimed-test gaps stay on PER-1563 (not for Tek unless he asks).

`github_writes=0` on origin until Kevin moves [PER-1596](https://linear.app/0ism/issue/PER-1596) Backlog→Todo. Research umbrella (Triage, no Todo): [PER-1595](https://linear.app/0ism/issue/PER-1595).

**Live HEAD (Bot Screen):** `77123c0ef3e1c24d6712a37720e912f3fc68d9b3`. Fourth round cherry-picked #109508 (`_fence()` before `_dispatch`). The hole in the first comment is **closed**.

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
