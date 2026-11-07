"""Engineering-first isolated later-stage resource coverage, local files only."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime

from run_long_budget_bridge import ROOT, rows, write_once, execute, controller_lock
from research.semantic_repair.evidence import digest
from explicit_resource_design import design, prepare, STEMS
from explicit_resource_build import build
from explicit_resource_analysis import analyze


def run_entry(root, cp, stem, entry, phase):
    folder = root / stem; inputs = folder / 'inputs'
    command = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, f'research.dynamic.{entry}',
               str(inputs / f'{stem}.txt'), str(inputs / 'RECONSTRUCTED-setup.txt'),
               str(inputs / 'fatigue-input.txt'), str(folder / 'cases.tsv'), str(folder / phase)]
    write_once(folder / f'{phase}-command.json', command)
    print('EXPLICIT_RESOURCE_START', stem, phase, flush=True)
    execute(command, folder / f'{phase}.log')
    return rows(folder / phase / 'receipt.jsonl')[0]


def main():
    root = ROOT / 'runs' / datetime.now().strftime('explicit-resource-witness-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('EXPLICIT_RESOURCE_ROOT', root, flush=True)
    completed = []
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            protocol = design(); write_once(root / 'protocol.json', protocol)
            cp = build(root)
            for stem in STEMS: prepare(root, stem)
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
                       for stem in STEMS for p in (root / stem / 'inputs').glob('*') if p.is_file()})
            engineering = []
            for stem in STEMS:
                receipt = run_entry(root, cp, stem, 'ExplicitResourceEngineering', 'engineering')
                assert receipt['status'] == 'PASS' and receipt['sourceCases'] == 64
                assert receipt['offlineFullDecodes'] == 192
                assert receipt['engineeringSuccessfulFE'] == 5 and receipt['expectedFailedFE'] == 1
                engineering.append(receipt)
            write_once(root / 'engineering-gate.json', {'status': 'PASS', 'instances': engineering,
                       'successfulFE': 10, 'expectedFailedFE': 2, 'offlineFullDecodes': 384})
            specs = {spec['stem']: spec for spec in protocol['instances']}
            paid, original_qa, independent, rejected = 0, 0, 0, 0
            for stem in STEMS:
                receipt = run_entry(root, cp, stem, 'ExplicitResourceWitness', 'witness')
                assert receipt['status'] == 'COMPLETE'
                assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['plannedFE']
                assert receipt['failedFE'] == 0
                paid += receipt['successfulFE']; original_qa += receipt['offlineOriginalFullQA']
                independent += receipt['independentTimelineValidations']
                rejected += receipt['expectedOriginalPolicyRejections']
                result = analyze(root, specs[stem]); completed.append(result)
                print('EXPLICIT_RESOURCE_ANALYZED', stem, 'eligible', result['worthRepresentationSearchDesign'], flush=True)
            worth = all(r['worthRepresentationSearchDesign'] for r in completed)
            write_once(root / 'analysis.json', {'instances': completed, 'worthRepresentationSearchDesign': worth})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': str(error),
                                         'completedInstances': [r['stem'] for r in completed]})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'witnessSuccessfulFE': paid,
        'engineeringSuccessfulFE': 10, 'expectedEngineeringFailedFE': 2, 'unexpectedEvaluationFailures': 0,
        'totalSuccessfulFE': paid + 10, 'totalAttemptedFE': paid + 12,
        'offlineOriginalFullQA': original_qa, 'engineeringOfflineFullDecodes': 384,
        'witnessIndependentTimelineValidations': independent, 'expectedLegacyPolicyRejections': rejected,
        'worthRepresentationSearchDesign': worth})
    print('EXPLICIT_RESOURCE_COMPLETE', 'worthRepresentationSearchDesign', worth, flush=True)


if __name__ == '__main__': main()
