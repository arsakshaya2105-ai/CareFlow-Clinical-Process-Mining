#!/usr/bin/env python3
"""Rule-based CareFlow conformance checker. Usage: python conformance_check.py input.csv --output-dir outputs"""
import argparse, json
from pathlib import Path
import pandas as pd
ALLOWED = {
    "registration": {"triage"},
    "triage": {"triage", "doctor consultation"},
    "doctor consultation": {"doctor consultation", "laboratory test", "x-ray", "treatment"},
    "laboratory test": {"doctor consultation"},
    "x-ray": {"doctor consultation"},
    "treatment": {"discharge"},
    "discharge": set(),
}
def check(input_csv, output_dir):
    df=pd.read_csv(input_csv)
    required={"case_id","event_id","activity_name","event_timestamp"}
    if not required.issubset(df.columns): raise ValueError(f"Missing columns: {required-set(df.columns)}")
    df["event_timestamp"]=pd.to_datetime(df["event_timestamp"],utc=True,errors="coerce")
    df["activity_name"]=df["activity_name"].astype(str).str.strip().str.lower()
    df=df.dropna(subset=["event_timestamp"]).sort_values(["case_id","event_timestamp","event_id"])
    cases=[]; transitions=[]
    for case,g in df.groupby("case_id",sort=True):
        acts=g.activity_name.tolist(); ts=g.event_timestamp.tolist(); errors=[]
        if not acts or acts[0] != "registration": errors.append({"type":"unexpected_start","position":1,"detail":"Expected registration"})
        if not acts or acts[-1] != "discharge": errors.append({"type":"unexpected_end","position":len(acts),"detail":"Expected discharge"})
        for i,(a,b) in enumerate(zip(acts,acts[1:]),1):
            ok=b in ALLOWED.get(a,set())
            transitions.append({"case_id":case,"from_activity":a,"to_activity":b,"transition_position":i,"is_allowed":ok})
            if not ok: errors.append({"type":"unexpected_transition","position":i+1,"detail":f"{a} -> {b}"})
        repeats={a:int(n) for a,n in pd.Series(acts).value_counts().items() if n>1}
        cases.append({"case_id":case,"event_count":len(acts),"activity_sequence":" -> ".join(acts),"is_conforming":not errors,"violation_count":len(errors),"violations":json.dumps(errors),"repeated_activities":json.dumps(repeats),"journey_duration_minutes":round((ts[-1]-ts[0]).total_seconds()/60,2) if len(ts)>1 else 0})
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    c=pd.DataFrame(cases); t=pd.DataFrame(transitions)
    c.to_csv(out/"case_conformance_results.csv",index=False); t.to_csv(out/"transition_conformance_results.csv",index=False)
    summary={"cases_analyzed":int(c.case_id.nunique()),"events_analyzed":int(len(df)),"conforming_cases":int(c.is_conforming.sum()),"non_conforming_cases":int((~c.is_conforming).sum()),"case_conformance_rate_pct":round(float(c.is_conforming.mean()*100),2),"total_transitions":int(len(t)),"unexpected_transitions":int((~t.is_allowed).sum()),"transition_conformance_rate_pct":round(float(t.is_allowed.mean()*100),2),"method":"Rule-based trace and directly-follows conformance; not PM4Py token replay."}
    (out/"conformance_summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("input_csv"); p.add_argument("--output-dir",default="outputs"); a=p.parse_args(); check(a.input_csv,a.output_dir)
