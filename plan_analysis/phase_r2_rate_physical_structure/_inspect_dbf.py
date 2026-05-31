"""Phase R2 read-only DBF header + sample inspector. Does not modify any source file."""
import os, struct, glob, json

SRC = r"plan_analysis/source_data/reference_dbf"

def parse_header(path):
    with open(path, "rb") as f:
        hdr = f.read(32)
        version = hdr[0]
        nrec = struct.unpack("<I", hdr[4:8])[0]
        hsize = struct.unpack("<H", hdr[8:10])[0]
        rsize = struct.unpack("<H", hdr[10:12])[0]
        fields = []
        while True:
            fd = f.read(32)
            if not fd or fd[0] == 0x0D:
                break
            name = fd[0:11].split(b"\x00")[0].decode("ascii", "replace")
            fields.append((name, chr(fd[11]), fd[16], fd[17]))
        return version, nrec, hsize, rsize, fields

def read_rows(path, fields, hsize, rsize, nrec, limit=10**9):
    rows = []
    with open(path, "rb") as f:
        f.seek(hsize)
        for i in range(min(nrec, limit)):
            rec = f.read(rsize)
            if not rec or len(rec) < rsize:
                break
            if rec[0:1] == b"*":
                continue
            off = 1; vals = {}
            for (name, ftype, flen, fdec) in fields:
                vals[name] = rec[off:off+flen].decode("latin-1", "replace").strip()
                off += flen
            rows.append(vals)
    return rows

# dedup case-insensitive
seen = {}
for path in glob.glob(os.path.join(SRC, "*.dbf")) + glob.glob(os.path.join(SRC, "*.DBF")):
    seen[os.path.basename(path).lower()] = path

inventory = {}
for key in sorted(seen):
    path = seen[key]
    base = os.path.basename(path)
    version, nrec, hsize, rsize, fields = parse_header(path)
    rows = read_rows(path, fields, hsize, rsize, nrec)
    # population
    nonempty = {fn[0]: 0 for fn in fields}
    for r in rows:
        for k, v in r.items():
            if v not in ("", "0", "0.00", "0.000000", "00", "0000", "19000101"):
                nonempty[k] += 1
    inventory[base] = {"version": version, "nrec": nrec, "rsize": rsize,
                       "fields": [{"o": i+1, "name": n, "type": t, "len": l, "dec": d}
                                  for i,(n,t,l,d) in enumerate(fields)],
                       "ndata": len(rows), "nonempty": nonempty}
    print("=" * 80)
    print(f"{base}  records={nrec} datarows={len(rows)} recsize={rsize} fields={len(fields)}")
    print("  " + " | ".join(f"{f[0]}:{f[1]}{f[2]}.{f[3]}" for f in fields))
    print("  nonempty(meaningful): " + ", ".join(f"{k}={v}" for k,v in nonempty.items()))

json.dump(inventory, open(os.path.join("plan_analysis/phase_r2_rate_physical_structure","_dbf_inventory.json"),"w"), indent=1)

# CNTL paging proof on QuikCvs: dump all CNTL rows for one (PLAN,AGE,GENDER)
print("\n##### CNTL PAGING PROOF (QuikCvs) #####")
cv = seen.get("quikcvs.dbf")
v,n,h,r,fl = parse_header(cv)
rows = read_rows(cv, fl, h, r, n)
key=(rows[0]["PLAN"], rows[0]["AGE"], rows[0]["GENDER"])
for row in rows:
    if (row["PLAN"],row["AGE"],row["GENDER"])==key:
        cvs=[row[f"CV{i}"] for i in range(10)]
        print(f"  PLAN={row['PLAN']} AGE={row['AGE']} G={row['GENDER']} CNTL={row['CNTL']} -> {cvs}")

# distinct CNTL values per factor table
print("\n##### DISTINCT CNTL VALUES #####")
for base in ["quikcvs.dbf","quikdbs.dbf","quikdvs.dbf","quiknps.dbf"]:
    p=seen.get(base)
    if not p: 
        print(f"  {base}: NOT PRESENT"); continue
    v,n,h,r,fl=parse_header(p)
    rs=read_rows(p,fl,h,r,n)
    cntls=sorted(set(x.get("CNTL","") for x in rs))
    ages=sorted(set(x.get("AGE","") for x in rs))
    print(f"  {base}: CNTL={cntls} | AGE range {ages[:3]}..{ages[-3:]} | rows={len(rs)}")

# gps actual filename
print("\n##### GPS FILE #####")
for k in seen:
    if k.startswith("quikgps"):
        print(" ", seen[k])
