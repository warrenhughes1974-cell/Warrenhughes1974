"""R2 read-only linkage + code-value check. Does not modify source files."""
import struct, glob, os

SRC = r"plan_analysis/source_data/reference_dbf"

def parse(path):
    f = open(path, "rb"); hdr = f.read(32)
    nrec = struct.unpack("<I", hdr[4:8])[0]
    hsize = struct.unpack("<H", hdr[8:10])[0]
    rsize = struct.unpack("<H", hdr[10:12])[0]
    fields = []
    while True:
        fd = f.read(32)
        if not fd or fd[0] == 0x0D: break
        fields.append((fd[0:11].split(b"\x00")[0].decode("ascii", "replace"), chr(fd[11]), fd[16]))
    f.seek(hsize); rows = []
    for i in range(nrec):
        rec = f.read(rsize)
        if not rec or len(rec) < rsize: break
        if rec[0:1] == b"*": continue
        off = 1; v = {}
        for (n, t, l) in fields:
            v[n] = rec[off:off+l].decode("latin-1", "replace").strip(); off += l
        rows.append(v)
    return rows

seen = {os.path.basename(p).lower(): p for p in glob.glob(SRC + "/*.dbf") + glob.glob(SRC + "/*.DBF")}
gp = parse(seen["quikgps(3).dbf"]); plgp = parse(seen["quikplgp.dbf"])
seg = lambda r: (r["PLAN"], r["GENDER"], r["UWCLASS"], r["BAND"], r["ISSCNTRY"], r["ISSUEST"], r["EFFDATE"])
gpseg = set(seg(r) for r in gp); keyseg = set(seg(r) for r in plgp)
print("GP factor distinct segtuples:", len(gpseg))
print("GP key   distinct segtuples:", len(keyseg))
print("factor tuples WITH a matching key:", len(gpseg & keyseg))
print("factor tuples MISSING a key (orphan factors):", len(gpseg - keyseg))
print("key tuples with NO factors (empty keys):", len(keyseg - gpseg))
print("sample orphan factor segs:", list(gpseg - keyseg)[:3])
print("sample empty key segs:", list(keyseg - gpseg)[:3])
print("GENDER codes in GP factor:", sorted(set(r["GENDER"] for r in gp)))
print("UWCLASS codes in GP factor:", sorted(set(r["UWCLASS"] for r in gp))[:12])
print("BAND codes in GP factor:", sorted(set(r["BAND"] for r in gp)))
print("distinct PLANs (GP):", len(set(r["PLAN"] for r in gp)))
print("EFFDATE values (GP):", sorted(set(r["EFFDATE"] for r in gp))[:6])

tv = parse(seen["quikpltv.dbf"])
print("\nQUIKPLTV assumption rows:")
for r in tv[:6]:
    print("  PLAN", repr(r["PLAN"]), "MORT", repr(r["MORT"]), "RSVINT", repr(r["RSVINT"]),
          "RSVMETH", repr(r["RSVMETH"]), "INTMETHTV", repr(r["INTMETHTV"]),
          "STOREMEANS", repr(r["STOREMEANS"]), "CALCMIDS", repr(r["CALCMIDS"]))

cv = parse(seen["quikplcv.dbf"])
print("\nquikplcv assumption sample:")
for r in cv[:4]:
    print("  PLAN", repr(r["PLAN"]), "MORT", repr(r["MORT"]), "ETIMORT", repr(r["ETIMORT"]),
          "NFOINT", repr(r["NFOINT"]), "INTMETHCV", repr(r["INTMETHCV"]))

gd = parse(seen["quikplgd.dbf"])
print("\nquikplgd GENDER member list sample:")
for r in gd[:10]:
    print("  PLAN", repr(r["PLAN"]), "GDCODE", repr(r["GDCODE"]), "GDDESCR", repr(r["GDDESCR"]))
