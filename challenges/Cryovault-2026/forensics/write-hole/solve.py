#!/usr/bin/env python3
"""write-hole (Cryovault 2026, forensics) — end-to-end solve.

Three raw RAID5 member images with the md superblock scrubbed. Reassemble the
array, pull the burn-after-read sealing key out of the ext4 journal, repair the
records lost to a torn write using parity, decrypt, and reassemble the flag.

Usage:  ./solve.py [dir-with-bay0.img..bay2.img] [--array out.img]

Needs: pip install cryptography   (no mdadm, no loop mount, no root)
"""
import hashlib
import json
import os
import re
import struct
import sys
import zlib

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- array geometry -------------------------------------------------------
# No superblock survives, so all four of these were brute-forced: assemble
# every (chunk size x layout x disk order) and keep the one e2fsck calls clean.
DATA_OFFSET = 1 << 20        # mdadm 1.2 default; first 1 MiB of each bay is scrubbed
CHUNK = 32 * 1024            # == the sealed record size, which is the whole point
NDISKS, NDATA = 3, 2
LAYOUT = "left-symmetric"
ORDER = (1, 2, 0)            # array slot -> bay number


def parity_slot(stripe):
    """mdadm left-symmetric: parity walks right-to-left, data follows it."""
    return NDISKS - 1 - (stripe % NDISKS)


def slots(stripe):
    """(parity bay, [data bay per position]) for one stripe."""
    p = parity_slot(stripe)
    return ORDER[p], [ORDER[(p + 1 + i) % NDISKS] for i in range(NDATA)]


def load_bays(d):
    return [open(os.path.join(d, f"bay{i}.img"), "rb").read()[DATA_OFFSET:]
            for i in range(NDISKS)]


def assemble(bays):
    """Stripe the member disks back into the logical md device."""
    per_disk = len(bays[0]) // CHUNK
    out = bytearray(per_disk * NDATA * CHUNK)
    for lc in range(per_disk * NDATA):
        stripe, pos = divmod(lc, NDATA)
        _, data = slots(stripe)
        o = stripe * CHUNK
        out[lc * CHUNK:(lc + 1) * CHUNK] = bays[data[pos]][o:o + CHUNK]
    return bytes(out)


def chunk_at(bays, bay, stripe):
    o = stripe * CHUNK
    return bays[bay][o:o + CHUNK]


# --- artefacts ------------------------------------------------------------
def find_intent(array):
    """The write-ahead intent file: per-record SHA-256 written before the payload.

    Note /stage/isfc-stage.py contains the same key names in its source, so
    candidates are validated by actually decoding them."""
    dec = json.JSONDecoder()
    anchor = -1
    while True:
        anchor = array.find(b'"record_size"', anchor + 1)
        if anchor < 0:
            raise SystemExit("no intent file found")
        start = array.rfind(b"{", max(0, anchor - 4096), anchor)
        if start < 0:
            continue
        try:
            obj, _ = dec.raw_decode(
                array[start:anchor + 8192].decode("utf-8", "replace"))
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("records"), list):
            return obj


def find_keyslots(array):
    """/stage/.keyslot is unlinked after reading, but data=journal means every
    version of it is still sitting in the ext4 journal. Scan + CRC-filter."""
    out, i = [], 0
    while True:
        i = array.find(b"KSLT", i)
        if i < 0:
            return out
        blob = array[i:i + 64]
        if len(blob) == 64:
            magic, ver, job = struct.unpack(">4sB3xQ", blob[:16])
            key = blob[16:48]
            (crc,) = struct.unpack(">I", blob[48:52])
            if magic == b"KSLT" and ver == 1 and zlib.crc32(blob[:48]) == crc:
                out.append({"off": i, "job": job, "key": key,
                            "key_id": hashlib.sha256(key).hexdigest()[:16]})
        i += 1


def find_payload(array, intent):
    """Locate payload.bin by matching any intact record against the intent."""
    rec = intent["record_size"]
    for want_i, want in enumerate(intent["records"]):
        for off in range(0, len(array) - rec + 1, 4096):
            if hashlib.sha256(array[off:off + rec]).hexdigest() == want:
                return off - want_i * rec
    raise SystemExit("no intact record found; cannot anchor payload.bin")


# --- repair ---------------------------------------------------------------
def recover_records(bays, array, intent):
    """For each record: take the on-disk copy if it matches the intent hash,
    otherwise rebuild it as parity XOR the surviving sibling in its stripe."""
    rec = intent["record_size"]
    assert rec == CHUNK, "record size must equal chunk size for 1:1 repair"
    base = find_payload(array, intent)
    first_lc = base // CHUNK
    results = []
    for i, want in enumerate(intent["records"]):
        stripe, pos = divmod(first_lc + i, NDATA)
        pbay, data = slots(stripe)
        mine, mate = data[pos], data[1 - pos]
        on_disk = chunk_at(bays, mine, stripe)
        rebuilt = bytes(a ^ b for a, b in zip(chunk_at(bays, pbay, stripe),
                                              chunk_at(bays, mate, stripe)))
        if hashlib.sha256(on_disk).hexdigest() == want:
            how, blob, verified = "on-disk", on_disk, True
        elif hashlib.sha256(rebuilt).hexdigest() == want:
            how, blob, verified = "parity-rebuild", rebuilt, True
        else:
            how, blob, verified = "parity-rebuild (hash mismatch)", rebuilt, False
        results.append({"i": i, "stripe": stripe, "parity_bay": pbay,
                        "data_bay": mine, "mate_bay": mate, "how": how,
                        "verified": verified, "blob": blob})
    return base, results


# --- unseal ---------------------------------------------------------------
def unseal(key, job, idx, blob):
    """AES-GCM: nonce = job||idx, aad = payload.bin|job|idx. Returns
    (plaintext, authenticated). Falls back to raw CTR when the tag is gone --
    the record body can survive a torn write even when its tag does not."""
    nonce = struct.pack(">QI", job, idx)
    aad = b"payload.bin|%d|%d" % (job, idx)
    try:
        return AESGCM(key).decrypt(nonce, blob[12:], aad), True
    except Exception:
        ctr = Cipher(algorithms.AES(key),
                     modes.CTR(nonce + (2).to_bytes(4, "big"))).decryptor()
        return ctr.update(blob[12:-16]), False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    here = os.path.dirname(os.path.abspath(__file__))
    src = args[0] if args else os.path.join(here, "../../../../hackathon/write-hole")
    bays = load_bays(src)
    array = assemble(bays)
    if "--array" in sys.argv:
        dst = sys.argv[sys.argv.index("--array") + 1]
        open(dst, "wb").write(array)
        print(f"[+] logical array written to {dst} ({len(array)} bytes)")

    print(f"[+] assembled: RAID5 {LAYOUT}, chunk {CHUNK // 1024}K, "
          f"bay order {ORDER}, data offset {DATA_OFFSET // 1024}K")

    intent = find_intent(array)
    job = intent["job"]
    print(f"[+] intent: job {job}, {len(intent['records'])} records of "
          f"{intent['record_size']} B, key_id {intent['key_id']}")

    slots_found = find_keyslots(array)
    print(f"[+] {len(slots_found)} CRC-valid keyslots recovered from the journal:")
    for s in slots_found:
        tag = " <-- matches intent" if s["key_id"] == intent["key_id"] else ""
        print(f"      job {s['job']}  key_id {s['key_id']}{tag}")
    key = next((s["key"] for s in slots_found
                if s["job"] == job and s["key_id"] == intent["key_id"]), None)
    if key is None:
        raise SystemExit("no keyslot matches the intent key_id")
    print(f"[+] sealing key: {key.hex()}")

    base, recs = recover_records(bays, array, intent)
    print(f"[+] payload.bin at array offset {hex(base)}")
    for r in recs:
        print(f"      rec{r['i']}  stripe {r['stripe']:>3}  parity=bay{r['parity_bay']} "
              f"data=bay{r['data_bay']} mate=bay{r['mate_bay']}  {r['how']}")

    shards, parts = {}, 0
    for r in recs:
        pt, authed = unseal(key, job, r["i"], r["blob"])
        parts += 1
        if not authed:
            print(f"[!] rec{r['i']}: GCM tag unverifiable -- plaintext recovered "
                  f"unauthenticated (torn parity cost the tag)")
        for m in re.finditer(rb"\[custody-token\] shard (\d)/(\d) = (\S+)", pt):
            shards[int(m.group(1))] = m.group(3).decode()

    print(f"[+] {parts} report parts unsealed, {len(shards)} token shards found")
    for k in sorted(shards):
        print(f"      shard {k}/3 = {shards[k]}")
    print("\nFLAG: " + "".join(shards[k] for k in sorted(shards)))


if __name__ == "__main__":
    main()
