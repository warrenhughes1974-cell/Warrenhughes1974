"""One-shot raw byte verification that L10 LP9595 and L01 10Y NP rows are absent from the delivered extracts."""
paths = [
    r"plan_analysis\source_data\rates\Rate_Table_Extract_20260427.csv",
    r"plan_analysis\source_data\rates\PAAGERAT_AttainedAge_Rates_Extract_20260428.csv",
]
needles = [b"9595", b"LP9595", b"L01 10Y", b"L01 10Y LT", b"L01 10Y MA", b"LP95"]
for p in paths:
    data = open(p, "rb").read()
    up = data.upper()
    print(p)
    print("  total bytes:", len(data))
    for n in needles:
        print(f"  occurrences of {n!r} (case-insensitive):", up.count(n.upper()))
    print()
