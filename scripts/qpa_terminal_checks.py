"""Post-acceptance zero-FE verification of the last paid phase and declared frozen artifacts."""
import json

from run_long_budget_bridge import rows, read
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest


def verify(root):
    cp = (root/'classpath.txt').read_text('utf-8-sig').strip()
    assert class_hashes(root/'classes') == read(root/'class-hashes.json')
    for name, sha in read(root/'source-hashes.json').items():
        assert digest(root/'source'/name) == sha
    checks = []
    for path in sorted(root.glob('*/*/receipt.jsonl')):
        receipt, = rows(path); last = None; models = []; end = None; paid = 0
        with (path.parent/'events.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                event = json.loads(line); end = event
                if event['kind'] in ('initial', 'step'):
                    paid += 1; last = event
                elif event['kind'] == 'model':
                    models.append(len(event['activeSubsets']))
        assert paid == receipt['successfulFE'] == last['paidFE']
        if last['kind'] == 'initial':
            assert receipt['stage'] == 'INITIALIZATION' and receipt['generation'] == 0
            assert receipt['slot'] == receipt['step'] == receipt['subset'] == receipt['donorSlot'] == receipt['reference'] == -1
            assert receipt['phase'] == 0 and not models
        else:
            for key in ('generation', 'slot', 'step', 'subset', 'phase', 'donorSlot', 'reference'):
                assert receipt[key] == last[key]
            assert receipt['stage'] == ('GENERATION_COMPLETE' if end['kind'] == 'generationEnd' else 'MIXING')
        capture, = rows(path.parent/'loaded-identity.jsonl'); verified = verify_capture(capture, cp)
        checks.append({'run': str(path.parent.relative_to(root)), 'successfulFE': paid, 'lastPaidPhase': receipt['phase'],
                       'activeMasksPerGeneration': models, 'recordedClassesVerified': len(verified), 'terminalFieldsExact': True})
    assert len(checks) == 14
    base = cp.split(';', 1)[1]
    for path in root.glob('*/PARITY-OLD-PA/loaded-identity.jsonl'):
        capture, = rows(path); verify_capture(capture, base)
    return {'passed': True, 'qpaRuns': checks, 'oldPAClassCaptures': 2, 'extraSearchFE': 0, 'decoderCalls': 0}
