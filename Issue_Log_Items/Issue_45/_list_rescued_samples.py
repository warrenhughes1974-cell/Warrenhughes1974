import pandas as pd, re
from pathlib import Path
EV=Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_45\evidence")
B=EV/"before_batch_v57.77"/"quikmstr.csv"
A=Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Output\quikmstr.csv")
b=pd.read_csv(B,dtype=str).fillna("")
a=pd.read_csv(A,dtype=str).fillna("")
bb=b[(b["MBILLFRM"].astype(str).str.strip()=="2")&(b["MBANKNO"].astype(str).str.strip()=="")][["MPOLICY"]].copy()
aa=a[["MPOLICY","MBANKNO"]].copy()
m=bb.merge(aa,on="MPOLICY",how="inner")
m=m[m["MBANKNO"].astype(str).str.strip()!=""]
prefer=["010157076C","010161748C","010348734C","010149834C","010154425C","010360289C","010367704C","010371356C","010374779C","010379477C","010379478C","010374837C"]
rows=[]
seen=set()
for p in prefer:
    r=m[m["MPOLICY"]==p]
    if len(r):
        rows.append(r.iloc[0]); seen.add(p)
for _,r in m.iterrows():
    if r["MPOLICY"] in seen: continue
    rows.append(r); seen.add(r["MPOLICY"])
    if len(rows)>=12: break

def mask(mb):
    aba,acct=mb.split("/",1)
    ad=re.sub(r"\D","",aba); cd=re.sub(r"\D","",acct)
    return "Account: ****%s  Routing: *****%s" % (cd[-4:], ad[-4:])

print("Total newly filled:", len(m))
print("")
for r in rows:
    print("%s  |  was blank  |  %s" % (r["MPOLICY"], mask(str(r["MBANKNO"]).strip())))
