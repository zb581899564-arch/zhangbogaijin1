"""Step 1: reuse all registered old paired fronts; no new evaluation or search."""
import argparse
from pathlib import Path
from common import *


def main(root):
    linux()
    payload = root / 'payload'
    for name, expected in read(payload / 'manifest.json').items():
        assert sha(payload / name) == expected['sha256'], name
    report = root / 'step1'
    report.mkdir()
    table, pair_table, facts = [], [], []
    for stem, scale in SCALES.items():
        paths = {(seed, arm): payload / 'historical' / stem / str(seed) / arm
                 for seed in (14910003, 14910037) for arm in ARMS}
        fronts = {key: checkpoints(folder) for key, folder in paths.items()}
        reference = nondominated([p for f in fronts.values() for p in f[500000]])
        write(report / (stem + '-reference.json'), reference.tolist())
        for seed in (14910003, 14910037):
            assert all(initial(paths[seed, arm]) == initial(paths[seed, ARMS[0]]) for arm in ARMS)
            common_fees = sorted(set.intersection(*(set(fronts[seed, arm]) for arm in ARMS)))
            for fe in common_fees:
                for arm in ARMS:
                    table.append(dict(instance=stem, seed=seed, arm=arm, fe=fe,
                                      **metrics(fronts[seed, arm][fe], reference, scale)))
                for control in ARMS[1:]:
                    a, b = fronts[seed, ARMS[0]][fe], fronts[seed, control][fe]
                    ma, mb = metrics(a, reference, scale), metrics(b, reference, scale)
                    denominator = ma['IGDplus'] + mb['IGDplus']
                    ca, cb = coverage(a, b), coverage(b, a)
                    pair_table.append(dict(instance=stem, seed=seed, fe=fe, control=control,
                        HVrelativePercent=100*(ma['HV']/mb['HV']-1),
                        IGDplusSymmetricImprovementPercent=200*(mb['IGDplus']-ma['IGDplus'])/denominator if denominator else 0,
                        CshareControl=ca['C'], CcontrolShare=cb['C'],
                        shareCCount=ca['covered'], controlCCount=cb['covered'],
                        shareFrontSize=cb['denominator'], controlFrontSize=ca['denominator']))
            for arm in ARMS:
                receipt, = rows(paths[seed, arm] / 'run-receipt.jsonl')
                assert receipt['successful'] == receipt['attempted'] == 500000 and receipt['failed'] == 0
                facts.append(dict(instance=stem, seed=seed, arm=arm, paidDigestAvailable=receipt['paidSHA256'] is not None,
                    checkpointFEs=common_fees, phaseFees={k: v for k,v in receipt['search'].items() if k.endswith('.evaluations')}))
    csv_write(report / 'metrics.csv', table)
    csv_write(report / 'paired.csv', pair_table)
    write(report / 'acceptance.json', dict(newSearchFE=0, newDecoderQA=0, historicalRuns=12,
        sharedInitials=True, referenceRule='All 3 methods x both old seeds final ND union, per instance',
        timingComparison=False, facts=facts,
        missing=['Strong control paid candidate acceptance and ancestry', 'Matched control working population lifecycle'],
        captureInstance='100_2_3_1', captureSeed=14910003,
        selectionReason='Existing large-job failure structure; first old registered seed; no new favorable seed',
        limitation='Checkpoint association cannot identify a causal search difference'))
    print('STEP1_DONE', len(table), len(pair_table), 'new FE 0')
    for row in pair_table:
        if row['instance']=='100_2_3_1' and row['seed']==14910003 and row['fe']>=50000:
            print(row)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('root', type=Path)
    main(parser.parse_args().root)
