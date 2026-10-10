# RAID5 write hole

**In one line:** a RAID5 stripe update is two or more separate writes (data, parity) with no
atomicity between them, so a power loss mid-update leaves a stripe where data and parity
disagree — and the array has no way to know which of the two is the stale one.

Hit in: [write-hole](../../challenges/Cryovault-2026/forensics/write-hole/README.md)
(Cryovault 2026, forensics).

## Why it exists

To update one chunk, RAID5 must write the chunk **and** recompute and write the stripe's
parity. Those are independent writes to independent devices. Lose power between them and
the stripe is internally inconsistent:

| What landed | Consequence |
|---|---|
| data, not parity | parity is stale; a later disk failure "recovers" garbage |
| parity, not data | the data chunk is stale, but parity holds the new value |
| neither | stripe is simply the old version — consistent, no damage |

The array cannot tell these apart after the fact. `D0 ^ D1 ^ P != 0` says *something* is
wrong; it never says *which* member is wrong. That ambiguity is the hole.

## Why it's the attacker's/forensicator's friend

If parity landed and the data write did not, the new data is still fully recoverable —
parity is a complete XOR record of it:

```
new_data = parity ^ surviving_sibling_chunk
```

So a torn write does not destroy the new content, it **relocates** it into the parity
chunk. On a 3-member array with one sibling that is a one-line recovery.

## What makes it visible

- **XOR all members at the same offset.** Stripes align across members in every standard
  layout, so a consistent array XORs to zero *everywhere* regardless of which disk holds
  parity in a given stripe. Non-zero stripes are either torn writes or never-written space
  (distinguish them by entropy: random fill vs. structured data).
- **No write-intent bitmap** (`bitmap: none`, often set "for perf") means nothing on disk
  records which stripes were in flight, so nothing bounds the damage.
- **Chunk size == application record size** is the dangerous-and-convenient case: each
  record occupies exactly one chunk, so a torn write loses whole records rather than
  corrupting a record stream. Nice for the application's integrity story; it also makes the
  per-record repair exact.

## The mitigations, and what each one gives up

| Mitigation | What it does |
|---|---|
| write-intent bitmap | records in-flight stripe regions, so resync only re-checks those |
| md journal / PPL | makes the stripe update atomic by logging it first |
| battery/flash-backed cache | completes the in-flight writes after power returns |
| full-stripe writes only | never does read-modify-write, so there is nothing to tear |
| ZFS / btrfs RAIDZ | copy-on-write: no in-place stripe update exists to tear |

## Checks worth running first

```bash
# 1. is it RAID5 at all, and where is the damage?
python3 -c "...XOR all members per chunk, report non-zero stripes..."

# 2. entropy per 4 KiB -> scrubbed/unwritten noise vs. real filesystem data
#    (also locates the mdadm 1.2 default 1 MiB data offset)

# 3. geometry: brute-force chunk x layout x disk order, validate with a real checker
e2fsck -fn candidate.img      # NOT a magic-number test: parity duplicates chunk 0
                              # whenever the third chunk is zeroed, so magic "works"
                              # for most wrong geometries
```
