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
        if chunk[0] == 0x0D:
            break
        name = chunk[0:11].split(b"\x00")[0].decode("latin-1")
        fields.append(
            {"name": name, "type": chr(chunk[11]), "len": chunk[16], "dec": chunk[17]}
        )
        pos += 32
    off = 1
    for f in fields:
        f["off"] = off
        off += f["len"]
    return b, nrec, hlen, rlen, fields


def get_rec(p: Path, want: str = "018495BC", phase: str = "2"):
    b, nrec, hlen, rlen, fields = parse(p)
    for i in range(nrec):
        rec = b[hlen + i * rlen : hlen + (i + 1) * rlen]
        mp = next(f for f in fields if f["name"] == "MPOLICY")
        ph = next(f for f in fields if f["name"] == "MPHASE")
        if (
            rec[mp["off"] : mp["off"] + mp["len"]].decode().strip() == want
            and rec[ph["off"] : ph["off"] + ph["len"]].decode().strip() == phase
        ):
            return rec, fields
    return None, None


def main():
    a = Path(r"c:\Users\warren\Desktop\DBF_Append_Tool\output\quikridr.dbf")
    g = Path(
        r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_55\uat\QUIKRIDR.DBF"
    )
    for phase in ("1", "2"):
        ra, fa = get_rec(a, phase=phase)
        rg, fg = get_rec(g, phase=phase)
        print(f"\nPHASE {phase} equal={ra == rg}")
        if ra is None or rg is None:
            print(" missing")
            continue
        diffs = [i for i, (ca, cg) in enumerate(zip(ra, rg)) if ca != cg]
        print(f" differing bytes: {len(diffs)}")
        seen = set()
        for f in fa:
            for i in diffs:
                if f["off"] <= i < f["off"] + f["len"] and f["name"] not in seen:
                    raw_a = ra[f["off"] : f["off"] + f["len"]]
                    raw_g = rg[f["off"] : f["off"] + f["len"]]
                    print(f"  {f['name']}: append={raw_a!r} good={raw_g!r}")
                    seen.add(f["name"])
                    break


if __name__ == "__main__":
    main()
