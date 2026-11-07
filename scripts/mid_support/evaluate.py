"""Sequential full evaluation in legacy evaluator's bounded batches; all costs retained."""
import argparse
from common import *


def batch(root, kind):
    if kind == 'paid':
        assert read(root/'qa-complete.json')['passed']
        assert read(root/'native-gate.json')['passed']
    receipts = []
    for source in sorted((root/'prepared'/kind).glob('*.tsv')):
        count = len(source.read_text().splitlines())
        folder = root/kind/source.stem
        execute(java(root, 'research.dynamic.CounterfactualRun')+input_args()+
                [str(source), str(folder), kind.upper(), str(count)], folder)
        r = read(folder/'receipt.json')
        assert r['pending'] is None and r['error'] is None and r['loaded']
        assert sum(1 for _ in stream(folder/'evaluations.jsonl')) == count
        if kind == 'qa':
            assert (r['attemptedQA'], r['passedQA'], r['failedQA']) == (count, count, 0)
            assert r['maxAbsoluteObjectiveError'] == [0, 0, 0] and r['exactBits']
        else:
            assert (r['attempted'], r['successful'], r['failed'], r['written']) == (count, count, 0, count)
            assert r['decoder']['dynamic.evaluations'] == count and r['decoder']['dynamic.reusedOperations'] == 0
        receipts.append(dict(batch=source.stem, receipt=r))
        print('BATCH_DONE', kind, source.stem, count, flush=True)
    total = sum(x['receipt']['attemptedQA' if kind == 'qa' else 'attempted'] for x in receipts)
    assert total == (600 if kind == 'qa' else 4608)
    write(root/(kind+'-complete.json'), dict(passed=True, attempted=total, successful=total, failed=0, receipts=receipts))


def main(root):
    assert read(root/'prepared/generation-gate.json')['passed']
    execute(java(root, 'research.dynamic.SupportFixture')+input_args()[:2]+
            [str(root/'prepared/native-fixture.tsv')], root/'native-fixture')
    log = (root/'native-fixture/run.log').read_text()
    assert 'SUPPORT_FIXTURE_PASSED 1536 evaluations=0' in log
    write(root/'native-gate.json', dict(passed=True, proposals=1536, evaluations=0))
    batch(root, 'qa')
    batch(root, 'paid')
    source = read(root/'source-gate.json')
    write(root/'accounting.json', dict(passed=True, sourceActualFE=250000, counterfactualActualFE=4608,
          totalActualFE=254608, failed=0, sourceCheckpointQA=source['extraQA'], importedSourceQA=600,
          totalExtraQA=source['extraQA']+600, candidateAndImportQAFullDecoder=True,
          sourceUsesFrozenExactIncrementalDecoder=True, sameTimeClaim=False))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root', type=Path);args=p.parse_args();linux();main(args.root)
