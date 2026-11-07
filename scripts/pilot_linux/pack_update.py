"""Development-only transport of explicitly selected project code; no evaluation."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/linux-pilot-evaluation-20261106-01'


def pack(destination):
    selected=[]
    for p in (ROOT/'scripts/pilot_linux').iterdir():
        if p.is_file() and p.suffix in ('.py','.md'):
            selected.append((p, 'scripts/'+p.name))
    for p in (ROOT/'src/algorithms/diagnostics/pilot').glob('*.java'):
        selected.append((p,'new-java/'+p.name))
    for p in (RUN/'payload/anchor/extra').glob('*'):
        selected.append((p,'anchor/extra/'+p.name))
    for folder in ('research/pilot_evaluation',):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and p.suffix in ('.py','.md','.json'):
                selected.append((p,p.relative_to(ROOT).as_posix()))
    for name in ('research/dynamic_benchmark/metrics.py','research/dynamic_benchmark/tri_indicators.py',
                 'research/expansion_audit/metrics.py','docs/小试评价与Linux阶段诊断协议-2026-11-06.md'):
        selected.append((ROOT/name,name))
    manifest={name:hashlib.sha256(p.read_bytes()).hexdigest() for p,name in selected}
    with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED) as archive:
        for p,name in selected:archive.write(p,name)
        archive.writestr('deployment-manifest.json',json.dumps(manifest,indent=2))
    print(json.dumps({'path':str(destination),'bytes':destination.stat().st_size,
                      'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    pack(parser.parse_args().output)
