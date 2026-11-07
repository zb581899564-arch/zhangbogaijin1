"""Reuse only completed engineering traces with exact numeric inputs, options and loaded class bytes."""
from pathlib import Path

from run_long_budget_bridge import read, rows, write_once
from research.semantic_repair.evidence import digest
from frozen_classpath_identity import resolve_class, verify_capture


def reusable(root, stem, label, cmd):
    source_root = read(root/'protocol.json').get('reuseCompletedEngineeringRoot')
    if not source_root:
        return None
    folder = Path(source_root)/stem/label
    if not (folder/'independent-replay.json').exists():
        return None
    receipt, = rows(folder/'receipt.jsonl')
    assert receipt['status'] == 'COMPLETE' and receipt['error'] is None
    assert read(folder/'independent-replay.json')['passed']
    old = read(folder/'command.json'); entry = cmd.index('research.dynamic.GomEngineeringRun')
    assert old.index('research.dynamic.GomEngineeringRun') == entry
    old_flags, new_flags = old[:entry], cmd[:entry]
    old_cp, new_cp = old_flags[old_flags.index('-cp')+1],new_flags[new_flags.index('-cp')+1]
    old_flags[old_flags.index('-cp')+1] = new_flags[new_flags.index('-cp')+1] = '<verified-classpath>'
    assert old_flags == new_flags and old[entry+5:] == cmd[entry+5:]
    for index in range(entry+1,entry+4):
        assert digest(Path(old[index])) == digest(Path(cmd[index]))
    capture, = rows(folder/'loaded-identity.jsonl'); checked = verify_capture(capture,old_cp)
    for name, actual in checked.items():
        assert actual['sha256'] == resolve_class(new_cp,name)['sha256'], ('Reuse byte identity differs',name)
    out = root/stem/label; out.mkdir()
    write_once(out/'reuse.json',dict(source=str(folder), exactInputOptionsAndClassBytes=True,
                                   extraSearchFE=0, originalReceiptPreserved=True))
    print('CTX_GOM_REUSE_COMPLETED',stem,label,receipt['successful'],flush=True)
    return folder
