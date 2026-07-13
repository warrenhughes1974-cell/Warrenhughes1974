"""Compare Append Tool QUIKRIDR.DBF packing vs known-good writer."""
from __future__ import annotations

from pathlib import Path


def parse(p: Path):
    b = p.read_bytes()
    nrec = int.from_bytes(b[4:8], "little")
    hlen = int.from_bytes(b[8:10], "little")
    rlen = int.from_bytes(b[10:12], "little")
    fields = []
    pos = 32
    while True:
        chunk = b[pos : pos + 32]
        if not chunk or chunk[0] == 0x0D:
            break
        name = chunk[0:11].split(b"\x00")[0].decode("latin-1")
        typ = chr(chunk[11])
        length = chunk[16]
        dec = chunk[17]
        fields.append({"name": name, "type": typ, "len": length, "dec": dec})
        pos += 32
    off = 1
    for f in fields:
        f["off"] = off
        off += f["len"]
    return b, nrec, hlen, rlen, fields


def show(label: str, path: str, want: str = "018495BC") -> None:
    p = Path(path)
    b, nrec, hlen, rlen, fields = parse(p)
    print(f"\n==== {label} nrec={nrec} rlen={rlen} ====")
    for i in range(nrec):
        rec = b[hlen + i * rlen : hlen + (i + 1) * rlen]
        mp = next(f for f in fields if f["name"] == "MPOLICY")
        pol = rec[mp["off"] : mp["off"] + mp["len"]].decode("latin-1")
        if pol.strip() != want:
            continue
        ph = next(f for f in fields if f["name"] == "MPHASE")
        phase = rec[ph["off"] : ph["off"] + ph["len"]].decode("latin-1").strip()
        print(f"-- phase {phase} delete={rec[0]!r} --")
        for fname in [
            "MPLAN",
            "MAGE",
            "MUNIT",
            "MVPU",
            "MPREM",
            "MSAVEUNIT",
            "MSAVEVPU",
            "MCV0",
        ]:
            f = next(f for f in fields if f["name"] == fname)
            raw = rec[f["off"] : f["off"] + f["len"]]
            text = raw.decode("latin-1")
            print(
                f"  {fname:10} len={f['len']} dec={f['dec']} "
                f"raw={raw!r} text={text!r}"
            )


def main() -> None:
    show(
        "APPEND OUTPUT",
        r"c:\Users\warren\Desktop\DBF_Append_Tool\output\quikridr.dbf",
    )
    show(
        "ISSUE55 GOOD",
        r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_55\uat\QUIKRIDR.DBF",
    )
    show(
        "Q CSO_TEST",
        r"Q:\CSO\CSO_TEST\quikridr.dbf",
    )


if __name__ == "__main__":
    main()
