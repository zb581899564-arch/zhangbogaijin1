"""Export finite-matrix diagnostics; never evaluate or feed points back to search."""
import argparse
from collections import defaultdict
import csv
from pathlib import Path
import time
from analyze import load_matrices
from cf_common import MATURE, OLD, STEMS, prepare, read, write
from evidence_audit import verify_cases


def table(path, rows):
    with path.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def metric_row(identity, scored, comparison):
    coverage = comparison['coverage']
    return dict(identity, frontSize=scored['frontSize'],
                HV=scored['HV']['1.5'], HV125=scored['HV']['1.25'], HV200=scored['HV']['2.0'],
                IGDplus=scored['IGDplus'], IGD=scored['IGD'],
                HVEffectPct=comparison['HVEffectPct']['1.5'],
                IGDplusSymmetricImprovementPct=comparison['IGDplusSymmetricImprovementPct'],
                **coverage)


def export_cases(output, results):
    cells, named, classifications = [], [], []
    for case in results:
        identity = {k: case[k] for k in ('id', 'instance', 'seed', 'arm', 'label', 'role', 'parentId')}
        for mask, objectives in enumerate(case['objectives']):
            row = dict(identity, mask=mask, Cmax=objectives[0], TEC=objectives[1], TWC=objectives[2])
            for background, profiles in case['gainProfiles'].items():
                for radius, profile in profiles.items():
                    row[f'{background}_HVgain_{radius}'] = profile['absolute'][mask]
                    row[f'{background}_HVgainPct_{radius}'] = profile['relativePct'][mask]
            cells.append(row)
        for name, values in case['namedMetrics'].items():
            named.append(metric_row(dict(identity, control=name, mask=values['mask']),
                                    values['metrics'], values['versusFull']))
        cls = case['classification']
        classifications.append(dict(identity,
            strictBetterSubsets=str(cls['strictBetterSubsets']),
            harmfulAtomsAtFull=str(cls['harmfulAtomsAtFull']),
            fullNecessaryBeforeEvent=cls['necessity']['beforeEvent']['fullNecessary'],
            minimalBeforeEvent=str(cls['minimalPositiveMasks']['beforeEvent']),
            mixedCertificates=str(cls['resourceOrderMinimalCertificates']),
            crossJobCertificates=str(cls['crossJobResourceOrderCertificates']),
            uniquePhysical=cls['uniquePhysical']))
    table(output / 'all-416-configurations.csv', cells)
    table(output / 'named-controls-156.csv', named)
    table(output / 'case-classifications-26.csv', classifications)


def source_unions(root, cases, matrices):
    """Describe oracle sets of unequal cardinality, not competing algorithms."""
    from analysis_metrics import frozen_scale, metrics, pair
    groups = defaultdict(list)
    for cid, case in cases.items():
        groups[case['instance'], case['seed'], case['arm']].append(cid)
    specs = {s['stem']: s for s in read(MATURE / 'protocol.json')['instances']}
    result, csv_rows = [], []
    configurations = dict(FULL=[15], RESOURCE=[3], ORDER=[12], JOB_A=[5], JOB_B=[10],
                          ORDINARY_UNION=[3, 12, 5, 10], ALL_COUNTERFACTUALS=list(range(16)))
    for (stem, seed, arm), ids in sorted(groups.items()):
        a0 = cases[ids[0]]['A0']
        assert all(cases[cid]['A0'] == a0 for cid in ids)
        scale = frozen_scale(specs[stem])
        reference = read(root / 'analysis' / (stem + '-reference.json'))
        final = read(OLD / 'science' / stem / str(seed) / arm / 'front.json')
        backgrounds = dict(A0=a0, previousFinal=final)
        for background_name, background in backgrounds.items():
            baseline = metrics(background, reference, scale)
            scored = {}
            for name, masks in configurations.items():
                points = [matrices[cid][m]['objectives'] for cid in ids for m in masks]
                scored[name] = metrics([*background, *points], reference, scale)
            for name, values in scored.items():
                identity = dict(instance=stem, seed=seed, arm=arm, background=background_name,
                                configuration=name, pairs=len(ids), masksPerPair=len(configurations[name]))
                vs_background = pair(seed, values, baseline)
                vs_full = pair(seed, values, scored['FULL'])
                vs_ordinary = pair(seed, values, scored['ORDINARY_UNION'])
                csv_rows.append(metric_row(identity, values, vs_full))
                result.append(dict(identity, metrics=values, versusBackground=vs_background,
                                   versusFull=vs_full, versusOrdinaryUnion=vs_ordinary))
    write(root / 'analysis' / 'diagnostic-source-unions.json', result)
    table(root / 'analysis' / 'diagnostic-source-unions.csv', csv_rows)
    return result


def source_costs(root):
    result = {}
    for phase in ('qa', 'paid'):
        receipt = read(root / (phase + '-complete.json'))
        process_seconds = sum(read(root / phase / stem / 'process.json')['seconds'] for stem in STEMS)
        result[phase] = dict(attempted=receipt['attempted'], successful=receipt['successful'],
                             failed=receipt['failed'], jvmWallSeconds=process_seconds,
                             javaBodySeconds=sum(r['processBodySeconds'] for r in receipt['receipts']))
    return result


def main(root):
    prepare()
    start = time.perf_counter()
    report = read(root / 'analysis' / 'report.json')
    protocol = read(root / 'protocol.json')
    cases = {c['id']: read(root / 'cases' / (c['id'] + '.json')) for c in protocol['cases']}
    matrices = load_matrices(root, protocol)
    audit = verify_cases(root, cases, matrices)
    export_cases(root / 'analysis', report['cases'])
    unions = source_unions(root, cases, matrices)
    positive = [c for c in report['cases'] if c['label'] == 'POSITIVE']
    ordinary = (3, 12, 5, 10)
    sufficient = [c['id'] for c in positive if max(
        c['gainProfiles']['beforeEvent']['1.5']['absolute'][m] for m in ordinary
    ) >= c['gainProfiles']['beforeEvent']['1.5']['absolute'][15] - protocol['hvNumericalAbsTol']]
    summary = dict(passed=True, groups=report['groups'], costs=source_costs(root), evidenceAudit=audit,
                   ordinaryHVAtLeastFullPositiveCases=sufficient,
                   sourceUnionRows=len(unions), exportAndUnionSeconds=time.perf_counter()-start,
                   originalAnalysisSeconds=report['seconds'], newDecoderCalls=0,
                   decision='LOCAL_EDIT_CERTIFICATES_ONLY_NO_MAINLINE_PROMOTION_OR_SCALE',
                   scope='Diagnostic unions use unequal numbers of points; no equal-budget algorithm claim')
    write(root / 'analysis' / 'delivery-summary.json', summary)
    print(summary, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
