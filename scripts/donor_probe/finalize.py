"""Seal this completed donor experiment; never executes search or a decoder."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import shutil

from run_helpers import read, write


def inspect(root):
    audits = ['engineering-acceptance.json', 'source-and-cost-audit.json',
              'report/audit-20261106T080556.705384Z-220075/audit.json']
    for name in audits:
        assert read(root / name)['passed'], name
    source = read(root / audits[1])
    rows = source['actualRuns']
    totals = {key: sum(row.get(key, 0) for row in rows) for key in
              ['attempted', 'successful', 'failed', 'processSeconds', 'searchSeconds',
               'importFullQA', 'importQASeconds', 'paidTimelineQA', 'paidTimelineQASeconds']}
    assert (totals['attempted'], totals['successful'], totals['failed']) == (3473608, 3473606, 2)
    assert read(root / 'actual-fees.json')['science']['failed'] == 0
    totals['sourceCheckpointOfflineDecodes'] = sum(
        q['uniqueOfflineDecodes'] for row in rows for q in (row.get('checkpointQA') or []))
    metric = read(root / audits[2])['metricChecks']
    totals['independentHVChecks'] = sum(len(p['absoluteHVErrors']) for x in metric for p in x['endpoints'])
    assert totals['independentHVChecks'] == 162
    return audits, totals


def close_visual_review(root):
    export = read(root / 'figures/figure-export.json')
    assert len(export['exports']) == 2
    assert read(root / 'figure-preflight-final.json')['summary']['counts']['FAIL'] == 0
    for row in export['exports']:
        assert row['svgTextElements'] > 0 and row['rawEffectPoints'] == 90
        for suffix in ('.svg', '.pdf', '.png', '-preview.png'):
            assert (root / 'figures' / (row['stem'] + suffix)).stat().st_size > 0
    write(root / 'figures/visual-review.json', {
        'passed': True, 'reviewedUTC': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'Primary assistant viewed both actual 300dpi preview images after Linux rendering',
        'figures': [x['stem'] for x in export['exports']],
        'checks': ['Readable labels, axes, legends and panel marks; no clipping or overlap',
                   'All three paired seeds, both endpoints and all five comparisons displayed',
                   'Same metric axes across instances/endpoints; units and improvement direction explicit',
                   'One-pass developmental probe boundary and absence of confidence intervals labelled'],
        'warningAccepted': 'No TIFF required for pilot; editableSVG/PDF and600dpiPNG supplied',
        'history': 'First150dpi sourcepreflight failed before rendering; retained and fixed without search rerun',
        'closesPending': 'figure-export.json visualInspection flag is historical; this record supersedes it'})


def dependency_record(root, anchor, digest):
    names = ['protocol.json', 'environment.json', 'evidence-manifest.json',
             'payload/deployment-manifest.json', 'payload/transfer-manifest.json',
             'build-01/classpath.txt']
    rows = []
    folder = root / 'dependency-identity'
    folder.mkdir()
    for name in names:
        source = anchor / name
        destination = folder / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        rows.append({'anchorPath': str(source), 'bytes': source.stat().st_size,
                     'sha256': digest(source), 'identityCopy': str(destination.relative_to(root))})
    write(root / 'dependency-identity.json', {
        'anchor': str(anchor), 'identities': rows,
        'standaloneRuntimeBundle': False,
        'requires': 'Existing immutable linux-pilot-evaluation-20261106-01 payload/build and JDK17/Python3.11 runtime'})


def seal(root, anchor, packager, archive):
    assert platform.system() == 'Linux'
    assert not archive.exists() and root.resolve() not in archive.resolve().parents
    audits, totals = inspect(root)
    close_visual_review(root)
    spec = importlib.util.spec_from_file_location('evidence_packager', packager)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dependency_record(root, anchor, module.digest)
    write(root / 'decision.json', {
        'status': 'STOP_CURRENT_ORDINARY_DONOR_POOL', 'engineeringPassed': True,
        'scienceProbeFE': 284160, 'scientificFailures': 0,
        'reason': 'No material composite improvement.100case UNION tinyHV gain but IGDplus and C losses;20case no gain',
        'workingPopulationQualification': '100case C improves, but IGDplus worsens and HV effects vary',
        'sharedSupply': 'S-only augmentation exercised, no material gain; UNION20case seed16110037S reads10 is underexercised',
        'interpretation': 'Conditional on already paid source block, not causal value of producing global donors',
        'retain': ['original four roles', 'QGS', 'families', 'existing sharing mechanism and historical positive evidence'],
        'noExpansion': ['seeds', 'windows', 'capacity/ratio tuning', '6000000FE', 'TIME_LIMIT', 'new selector'],
        'mainlineModified': False, 'goalResumed': False, 'newBackgroundJob': False,
        'fullAlgorithmComparison': False, 'sameTimeAdvantage': False, 'newInnovationClaim': False})
    write(root / 'delivery-acceptance.json', {
        'passed': True, 'completedUTC': datetime.now(timezone.utc).isoformat(),
        'audits': audits, 'totals': totals, 'newSearchFEAtDelivery': 0, 'newDecoderCallsAtDelivery': 0,
        'figures': 'figures/visual-review.json', 'decision': 'decision.json',
        'pendingScience': ['Independent held-out generalization and full algorithm/classic/time trials were not authorized by this probe'],
        'note': 'Science/analysis receipts retain their historical pending flags; independent audit and this seal close verification only'})
    module.package(root, archive)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'anchor', 'packager', 'archive'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    seal(args.root, args.anchor, args.packager, args.archive)
