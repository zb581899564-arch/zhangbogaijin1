"""Seal audited evidence and costs; no search, decode or quality calculation."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def summarize_costs(root, plan):
    stages = {}
    for stage in ('engineering', 'science'):
        paths = list((root / stage).glob('*/*/*/receipt.json'))
        rows = [read(path) for path in paths]
        stages[stage] = dict(runs=len(rows), **{k: sum(r[k] for r in rows)
            for k in ('attempted', 'successful', 'failed', 'searchSeconds', 'prepareSeconds')},
            timelineQACount=sum(r['physicsQA']['fullTimelineChecks'] for r in rows),
            timelineQASeconds=sum(r['physicsQA']['engineeringOnlySeconds'] for r in rows),
            importQACount=sum(r['importQA']['fullDecodes'] for r in rows),
            importQASeconds=sum(r['importQA']['offlineSeconds'] for r in rows),
            completeProcessSeconds=sum(read(p.parent / 'process.json')['seconds'] for p in paths),
            offlineAuditSeconds=read(root / (stage + '-independent-audit.json'))['offlineSeconds'])
    assert sum(s['attempted'] for s in stages.values()) == plan['totalPlannedAttemptedFE']
    assert stages['science']['successful'] == plan['scienceFE'] and stages['science']['failed'] == 0
    assert stages['engineering']['failed'] == 2
    assert sum(s['importQACount'] for s in stages.values()) == 1200
    return dict(stages=stages, sourceNewSearchFE=0, historicalSourcePaidFE=3000000,
                analysisSeconds=read(root / 'report/acceptance.json')['seconds'],
                plottingSeconds=read(root / 'report/figures/figure-export.json')['seconds'],
                observationSecondsSeparated=False,
                costQualification='Search includes observation and engineering physics QA; do not add its subsets again. Complete process includes startup/finalization. No same-time conclusion')


def snapshot_dependencies(root, bases):
    output = root / 'inherited-identity'
    output.mkdir()
    records = []
    for base in bases:
        for relative in ('protocol.json', 'environment.json', 'delivery-acceptance.json',
                         'evidence-manifest.json', 'build-01/identity.json', 'build-01/classpath.txt'):
            source = base / relative
            if not source.is_file():
                continue
            target = output / base.name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            records.append(dict(source=str(source), copiedAs=str(target.relative_to(root)),
                                sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    write(output / 'index.json', dict(records=records, completeRuntimeBundled=False,
        qualification='Reproduction also requires the preserved source and classpath packages named in these manifests'))


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'anchor', 'donor', 'packager', 'archive'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); root = args.root
    required = ['source-acceptance.json', 'engineering-runtime-acceptance.json',
                'engineering-independent-audit.json', 'science-complete.json',
                'science-independent-audit.json', 'report/acceptance.json',
                'report/figures/visual-review.json']
    for name in required:
        assert read(root / name)['passed'], name
    decision = read(root / 'report/decision.json')
    assert decision['mainlineChanged'] is False and decision['goalResumed'] is False
    assert decision['sameTimeAdvantageProved'] is False
    costs = summarize_costs(root, read(root / 'protocol.json'))
    write(root / 'cost-summary.json', costs)
    snapshot_dependencies(root, [args.anchor, args.donor])
    write(root / 'delivery-acceptance.json', dict(passed=True, completedUTC=datetime.now(timezone.utc).isoformat(),
        requiredReceipts=required, scientificRuns=18, scienceFE=639360, scienceFailures=0,
        engineeringInjectedFailures=2, statisticsPending=False, inheritedPendingFlagsAreHistorical=True,
        sourceSharedProposalCount=0, defaultMainlineModified=False, goalResumed=False,
        backgroundExperimentCreated=False, newSearchFEAtDelivery=0, newDecoderCallsAtDelivery=0,
        decision='report/decision.json', costSummary='cost-summary.json'))
    module_spec = importlib.util.spec_from_file_location('evidence_packager', args.packager)
    packager = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(packager)
    assert root.resolve() not in args.archive.resolve().parents
    packager.package(root, args.archive)


if __name__ == '__main__':
    main()
