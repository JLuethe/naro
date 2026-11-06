#!/usr/bin/env python3
"""Classify the existing 19-case search corpus with the unchanged identity policy."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'spec/tools'))
from identity_review import classify, policy_identity, summary_counts

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    parser.add_argument('candidate',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    cases=json.loads((ROOT/'spec/evidence/scenarios/search.json').read_text())
    rows={}
    for case in cases:
        tid=case['id']
        reference=json.loads((args.reference/tid/'result.json').read_text())
        candidate=json.loads((args.candidate/tid/'result.json').read_text())
        row=classify(reference,candidate,tid,case)
        rows[tid]=row
        print(tid,row['classification'])
    summary=summary_counts(rows)
    args.out.write_text(json.dumps(dict(policy=policy_identity(),summary=summary,cases=rows),indent=2)+'\n')
    print(summary)
    return int(summary['unexpected']>0 or summary['accepted']!=len(cases))

if __name__=='__main__':raise SystemExit(main())
