"""Build L5 for the frozen ten or an explicitly selected local month dataset."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.apps.analysis.sampling import has_snapshot
from src.apps.analysis.longitudinal.services import prepare_match, aggregate_signatures, save_analysis
from src.apps.analysis.longitudinal.retrieval import compact_packet, size
from src.apps.analysis.numeric.storage import write_json


def run(*, dataset_path: Path | None, label: str, reuse_signatures: bool = False) -> dict:
    dataset=json.loads(dataset_path.read_text(encoding='utf-8')) if dataset_path else None
    selection=dataset or json.loads((ROOT/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    ids=[r['match_id'] for r in dataset['matches']] if dataset else [int(mid) for mid in selection['lower_outputs']]
    directory=ROOT/'data/analysis/longitudinal'/label;rows=[];paths=[];missing=[]
    index_path=directory/'signatures.json'
    if reuse_signatures:
        index=json.loads(index_path.read_text(encoding='utf-8'))
        for path in index['paths']:rows.append(json.loads((ROOT/path).read_text(encoding='utf-8')))
        paths=index['paths'];missing=index['missing']
        if {r['match_id'] for r in rows}|set(missing)!=set(ids):raise ValueError('Signature index and selected scope differ')
    else:
        for i,mid in enumerate(ids,1):
            if not all(has_snapshot(ROOT,mid,s) for s in ('opendota','stratz')):missing.append(mid);continue
            print(f'L4 {i}/{len(ids)}: {mid}',flush=True)
            result=prepare_match(root=ROOT,account_id=selection['account_id'],match_id=mid,dataset_path=dataset_path)
            rows.append(result['signature']);paths.append((result['directory']/'signature.json').relative_to(ROOT).as_posix())
        write_json(index_path,{'paths':paths,'missing':missing})
    data,detail=aggregate_signatures(rows,dataset=dataset,recent_count=max(1,min(10,len(rows)//3)))
    save_analysis(directory,data,detail);packet=compact_packet(data);write_json(directory/'packet.json',packet)
    verification={'selected':len(ids),'analyzed':len(rows),'missing':missing,'l5_revision':data['revision'],
                  'cohorts':len(data['cohorts']),'candidates':data['relations']['candidate_count'],
                  'replicated':data['relations']['replicated_count'],'packet_bytes':size(packet),
                  'output':directory.relative_to(ROOT).as_posix(),'meta_applied':False}
    write_json(ROOT/f'data/prototype/longitudinal-{label}-verification.json',verification)
    print(json.dumps(verification),flush=True)
    return verification


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path);p.add_argument('--label',default='ten')
    p.add_argument('--reuse-signatures',action='store_true');a=p.parse_args()
    if not a.label.replace('-','').isalnum():p.error('Label must be alphanumeric with optional hyphens')
    run(dataset_path=a.dataset,label=a.label,reuse_signatures=a.reuse_signatures)
