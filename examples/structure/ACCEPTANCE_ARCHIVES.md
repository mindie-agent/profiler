# Compact acceptance publications

The current priority JSON contains selected Decode comparisons, latest attempts,
operator accuracy tiers and SHA256 evidence pointers. Its Markdown companion
retains the full readable tables. `full_evidence` points to the immutable complete
scoreboard, including every historical attempt, native contract and layer detail.
`review_priority_decode_scoreboard.py` verifies both the projection and full data.

`acceptance-archive-index.json` records large historical artifacts removed from
Git tracking. Local original paths remain available to existing replay commands;
their byte-identical copies live under
`/Volumes/data/mindie-sim-data/acceptance-archives-20261030/objects/`.
These captures are external acceptance data, not package or wheel dependencies.
An absent archive is explicitly unavailable, never an empty successful replay.

To regenerate a compact publication:

```sh
python examples/structure/priority_decode_scoreboard.py \
  --input-manifest examples/structure/acceptance-20261030-priority/priority-scoreboard-inputs.json \
  --output examples/structure/acceptance-20261030-priority/priority-three-level-scoreboard.json \
  --archive-root /Volumes/data/mindie-sim-data/acceptance-archives-20261030/scoreboards
```

New large evidence can be archived with `archive_acceptance.py --archive-root
PATH --apply`. SHA256 objects are verified before Git tracking is removed. Raw
profiling captures are never deleted. Full historical replays require the linked
external files and the declared companion Sim runtime.

The current source-corrected Decode result is 65/66; Qwen3.5-397B c48 is retained
as a failed comparison after correcting its shared-expert precision. Retrospective
concurrency holdout validation is separate: 144/150 operator domains and 2/6 Body
cases pass. Neither in-sample accuracy nor an unavailable capture implies blind
generalization or complete client TPOT accuracy.
