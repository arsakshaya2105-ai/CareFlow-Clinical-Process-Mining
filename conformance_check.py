"""Rule-based conformance check for CareFlow's documented reference pathway.
Run: python process_mining/conformance_check.py --input data/careflow_cleaned_event_logs.csv --output process_mining/outputs
This is a transparent, configurable transition-rule check, not PM4Py token replay.
"""
import argparse
from pathlib import Path
import pandas as pd

ALLOWED = {
    ("registration", "triage"),
    ("triage", "doctor consultation"),
    ("triage", "triage"),  # repeat triage / reassessment
    ("doctor consultation", "doctor consultation"),  # repeat consultation
    ("doctor consultation", "laboratory test"),
    ("doctor consultation", "x-ray"),
    ("doctor consultation", "treatment"),
    ("doctor consultation", "discharge"),
    ("laboratory test", "doctor consultation"),
    ("x-ray", "doctor consultation"),
    ("treatment", "discharge"),
}
START = "registration"
END = "discharge"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', default='data/careflow_cleaned_event_logs.csv')
    ap.add_argument('--output', default='process_mining/outputs')
    args = ap.parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.input)
    df.columns = [c.strip().lower() for c in df.columns]
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['case_id','activity_name','event_timestamp'])
    df['activity_name'] = df['activity_name'].astype(str).str.strip().str.lower()
    df = df.sort_values(['case_id','event_timestamp','event_id'])
    transitions=[]; cases=[]
    for case, g in df.groupby('case_id', sort=False):
        acts=g.activity_name.tolist()
        violations=[]
        if not acts or acts[0] != START: violations.append(f'Invalid start: {acts[0] if acts else "EMPTY"}')
        if not acts or acts[-1] != END: violations.append(f'Invalid end: {acts[-1] if acts else "EMPTY"}')
        for a,b in zip(acts,acts[1:]):
            ok=(a,b) in ALLOWED
            transitions.append({'case_id':case,'from_activity':a,'to_activity':b,'conforms':ok})
            if not ok: violations.append(f'Unexpected transition: {a} -> {b}')
        cases.append({'case_id':case,'event_count':len(acts),'start_activity':acts[0] if acts else '',
                      'end_activity':acts[-1] if acts else '', 'conforms':len(violations)==0,
                      'violation_count':len(violations),'violations':' | '.join(violations)})
    t=pd.DataFrame(transitions); c=pd.DataFrame(cases)
    t.to_csv(out/'conformance_transition_details.csv',index=False)
    c.to_csv(out/'conformance_case_results.csv',index=False)
    summary=pd.DataFrame([{
      'cases_checked':len(c),'conforming_cases':int(c.conforms.sum()),
      'nonconforming_cases':int((~c.conforms).sum()),
      'case_conformance_pct':round(c.conforms.mean()*100,2) if len(c) else 0,
      'transitions_checked':len(t),'conforming_transitions':int(t.conforms.sum()),
      'nonconforming_transitions':int((~t.conforms).sum()),
      'transition_conformance_pct':round(t.conforms.mean()*100,2) if len(t) else 0,
    }])
    summary.to_csv(out/'conformance_summary.csv',index=False)
    print(summary.to_string(index=False))
    if len(t): print('\nUnexpected transitions:\n',t[~t.conforms].groupby(['from_activity','to_activity']).size().sort_values(ascending=False).to_string())
    print('\nNOTE: Reference rules are an explicit project assumption. Review with a clinical/process owner before interpreting deviations.')
if __name__=='__main__': main()
