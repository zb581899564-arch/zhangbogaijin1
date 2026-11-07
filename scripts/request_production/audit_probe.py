"""Independent evidence-only conditional production audit; no Java or physical decode."""
import argparse
from functools import lru_cache
import hashlib
from pathlib import Path
import sys
import time
from urllib.parse import unquote, urlparse
import zipfile

sys.dont_write_bytecode = True
from common import SOURCE, STEMS, SEEDS, read, sha, write, linux
from audit_inputs import ARMS, lines, load_context, require, same
from audit_moves import replay


@lru_cache(maxsize=None)
def resolved_class(classpath, name):
    relative = name.replace('.', '/')+'.class'
    for part in classpath.split(':'):
        path = Path(part)
        if path.is_dir() and (path/relative).is_file():
            return sha(path/relative), (path/relative).resolve(), None
        if path.is_file() and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                if relative in archive.namelist():
                    return hashlib.sha256(archive.read(relative)).hexdigest(), path.resolve(), relative
    raise AssertionError('Unresolved runtime class '+name)


def verify_build(root):
    build = root/'probe-build-01'; identity = read(build/'identity.json')
    same(identity['inheritedClasspath'], (SOURCE/'build-01/classpath.txt').read_text().strip(), 'Probe inherited classpath changed')
    same(identity['sourceAcceptanceSHA256'], sha(SOURCE/'delivery-acceptance.json'), 'Source acceptance identity changed')
    classes = {p.relative_to(build/'classes').as_posix(): sha(p) for p in (build/'classes').rglob('*.class')}
    same(classes, identity['classes'], 'Probe compiled class manifest differs')
    manifest = root/'capture-build-01/dependencies.json'
    dependencies = read(manifest)
    same([r['path'] for r in dependencies], identity['inheritedClasspath'].split(':'), 'Inherited dependency order differs')
    for entry in dependencies:
        path = Path(entry['path'])
        actual = [p.relative_to(path).as_posix() for p in sorted(path.rglob('*')) if p.is_file()] if path.is_dir() else [path.name]
        same(actual, [r['path'] for r in entry['files']], 'Inherited dependency inventory changed')
        for item in entry['files']:
            file = path/item['path'] if path.is_dir() else path
            same((file.stat().st_size, sha(file)), (item['bytes'], item['sha256']), 'Inherited dependency bytes changed')
    return (build/'classpath.txt').read_text().strip(), dict(buildIdentitySHA256=sha(build/'identity.json'), dependencyManifestSHA256=sha(manifest))


def verify_loaded(receipt, classpath):
    critical = {'research.dynamic.RequestProductionRun', 'org.uma.jmetal.util.research.search.RequestProductionReplay',
                'org.uma.jmetal.util.research.search.RequestAcceptance', 'org.uma.jmetal.util.research.cooperation.RequestPoolAccess',
                'org.uma.jmetal.util.research.cooperation.FactoryPool', 'org.uma.jmetal.util.research.search.GomWorkspace',
                'org.uma.jmetal.util.research.search.GomDomainModels', 'org.uma.jmetal.util.research.modelglobal.PaMixingMove',
                'org.uma.jmetal.util.research.DynamicEvaluation', 'org.uma.jmetal.util.research.runtime.BudgetedProblem'}
    require(critical.issubset(receipt['loaded']), 'Missing actual loaded class identity')
    for name, item in receipt['loaded'].items():
        if not isinstance(item, dict):
            continue
        digest, path, member = resolved_class(classpath, name)
        same(item['sha256'], digest, 'Actual loaded SHA differs: '+name)
        resource = item['resource']
        if member is not None:
            require(resource.startswith('jar:'), 'Expected JAR class resource')
            location, relative = resource[4:].split('!/', 1)
            same(relative, member, 'JAR member differs')
        else:
            location = resource
        same(Path(unquote(urlparse(location).path)).resolve(), path, 'Actual class resource origin differs: '+name)


def validate_receipt(folder, receipt, category, stem, seed, q, label, classpath, context):
    failed = label == 'FAIL_2'; limit = int(label[4:]) if label.startswith('CUT_') else 512
    successful = 1 if failed else limit; arm = label if label in ARMS else 'REQUEST'
    same((receipt['arm'], receipt['sourceSeed'], receipt['requestIndex']), (arm, int(seed), int(q)), 'Run identity differs')
    same(receipt['seed'], int(seed) ^ 0x37a9185b ^ (int(q)*0x9e3779b9), 'Probe RNG seed differs')
    same((receipt['attempted'], receipt['successful'], receipt['failed'], receipt['feLimit']),
         (2 if failed else limit, successful, int(failed), limit), 'Attempt/success/failure/limit accounting differs')
    same((receipt['productionPaid'], receipt['assemblyPaid']), (min(successful, 511), int(successful == 512)), 'Production/assembly charging differs')
    same((receipt['plannedProductionFE'], receipt['plannedTotalFE']), (511, 512), 'Frozen production/assembly budget changed')
    same(receipt['stage'], 'COMPLETE' if successful == 512 else 'PRODUCTION', 'Run stopped in unexpected stage')
    same(receipt['actualRequest'], context['actual'], 'Actual request differs')
    same(receipt['observer'], label != 'OBSERVER_OFF', 'Observer setting differs')
    require((receipt['error'] is not None) == failed, 'Unexpected failure or missing expected failure')
    same(read(folder/'process.json')['exitCode'], int(failed), 'Process exit code differs')
    if category == 'engineering':
        same(receipt['physicsQA']['fullTimelineChecks'], successful, 'Missing full paid timeline QA')
        same(receipt['searchClockIncludesPaidEngineeringQA'], True, 'Engineering QA time accounting changed')
    else:
        same(receipt['searchClockIncludesPaidEngineeringQA'], False, 'Science unexpectedly includes paid engineering QA')
    imported = receipt['importQA']
    same((imported['sourcePointFullDecodes'], imported['importObjectiveMatches']), (102, 102), 'Import full-decode QA count differs')
    same(imported['retainedRecordFullDecodes'], sum(map(len, context['pools'])), 'Retained import QA count differs')
    same((imported['importedCandidatesOfferedToArchive'], imported['qaCombinationsOfferedToArchive']), (0, 0), 'Unpaid import QA entered archive')
    command = read(folder/'command.json')
    same(command[command.index('-cp')+1], classpath, 'Run command classpath differs')
    verify_loaded(receipt, classpath)


def engineering_pairs(base):
    for stem in STEMS:
        folder = base/stem/str(SEEDS[0])/'0'; reference = folder/'REQUEST'
        original = read(reference/'receipt.json')
        for label in ('REPEAT', 'OBSERVER_OFF'):
            other = folder/label; receipt = read(other/'receipt.json')
            same(receipt['paidSHA256'], original['paidSHA256'], 'Repeat/observer paid digest differs')
            for file in ('before.json', 'models.json', 'after.json', 'front.json', 'final-pools.json', 'assembly.json'):
                same(read(other/file), read(reference/file), 'Repeat/observer evidence differs: '+file)
        for label in ('OBSERVER_OFF',):
            same(lines(folder/label/'paid.jsonl'), [], 'Observer-off emitted paid rows')
            same(lines(folder/label/'steps.jsonl'), [], 'Observer-off emitted step rows')
            same(read(folder/label/'receipt.json')['paidLogRows'], 0, 'Observer-off log counter differs')
        for label, count in (('CUT_1', 1), ('CUT_2', 2), ('CUT_511', 511), ('FAIL_2', 1)):
            for file in ('steps.jsonl', 'paid.jsonl'):
                same(lines(folder/label/file), lines(reference/file)[:count], 'Cutoff/failure is not exact REQUEST prefix')
        for arm in ARMS:
            for file in ('before.json', 'models.json', 'initial-pools.json'):
                same(read(folder/arm/file), read(reference/file), 'Matched arm initial state/model/pool differs')


def run_audit(root, category):
    linux()
    started = time.perf_counter(); results = []
    destination = root/(category+'-independent-audit.json')
    require(not destination.exists(), 'Audit output already exists; never overwrite retained evidence')
    try:
        amendment = read(root/'amendment-01.json') if (root/'amendment-01.json').exists() else {}
        directory = amendment.get('inputDirectory', 'inputs'); request_count = amendment.get('requestsPerSource', 4)
        science_runs = amendment.get('scienceRuns', 2*3*request_count*4)
        request_audit = root/('request-audit-v2.json' if amendment else 'request-audit.json')
        require(read(request_audit)['passed'], 'Source request evidence gate failed')
        if amendment:
            same(amendment['probeFEAtAmendment'], 0, 'Sampling amendment occurred after probe performance')
            same(amendment['requestCycles'], [0, 4, 8], 'Sampling amendment cycles differ')
        classpath, identity = verify_build(root)
        sys.path.insert(0, str(SOURCE/'analysis-code'))
        from audit_genome import JavaRandom, collect_catalog, physical, verify_encoding, verify_mix
        from audit_replay import ParetoLedger, update_paid_digest
        helpers = dict(JavaRandom=JavaRandom, collect_catalog=collect_catalog, physical=physical,
                       verify_encoding=verify_encoding, verify_mix=verify_mix, ParetoLedger=ParetoLedger,
                       update_paid_digest=update_paid_digest)
        base = root/category
        if not base.is_dir():
            base = root/'runs'/category
        labels = ARMS + ('REPEAT', 'OBSERVER_OFF', 'CUT_1', 'CUT_2', 'CUT_511', 'FAIL_2')
        expected = {(stem, str(seed), str(q), label) for stem in STEMS
                    for seed in (SEEDS[:1] if category == 'engineering' else SEEDS)
                    for q in ([0] if category == 'engineering' else range(request_count))
                    for label in (labels if category == 'engineering' else ARMS)}
        observed = {tuple(path.parent.relative_to(base).parts) for path in base.glob('*/*/*/*/receipt.json')}
        same(observed, expected, 'Missing, duplicate, or extra planned run paths')
        attempted = successful = failures = 0; contexts = {}
        for stem, seed, q, label in sorted(expected):
            folder = base/stem/seed/q/label; receipt = read(folder/'receipt.json')
            key = stem, seed, q
            if key not in contexts:
                contexts[key] = load_context(root, directory, *key)
            context = contexts[key]
            if amendment:
                same(context['captured']['cycle'], amendment['requestCycles'][int(q)], 'Input q does not map to amended source cycle')
            validate_receipt(folder, receipt, category, stem, seed, q, label, classpath, context)
            details = replay(folder, context, receipt, helpers) if label != 'OBSERVER_OFF' else dict(observerComparedToRequest=True)
            results.append(dict(instance=stem, sourceSeed=int(seed), requestIndex=int(q), label=label, **details))
            attempted += receipt['attempted']; successful += receipt['successful']; failures += receipt['failed']
        if category == 'engineering':
            engineering_pairs(base)
            same((len(results), attempted, successful, failures), (20, 7176, 7174, 2), 'Engineering batch totals differ')
        else:
            same((len(results), attempted, successful, failures), (science_runs, science_runs*512, science_runs*512, 0), 'Science batch totals differ')
        report = dict(passed=True, category=category, runs=len(results), attempted=attempted,
            successful=successful, failed=failures, inputDirectory=directory, requestsPerSource=request_count,
            amendmentSHA256=sha(root/'amendment-01.json') if amendment else None, **identity,
            requestAuditSHA256=sha(request_audit),
            independentRawPaidSHA=True, independentAcceptance=True, independentPoolOfferTruncation=True,
            independentFinalOriginalSelector=True, exactSeededProposalSchedule=True, independentAllPaidFront=True,
            limitations=['No additional physical decode; complete timeline validity relies on separately recorded engineering QA.',
                        'FOS maximum-average linkage checked with 3e-12 numeric tolerance; acceptance and pool choices use no epsilon.',
                        'Observer-off has no paid log; exact digest and all final artifacts are compared with independently replayed REQUEST.'],
            helpers={name: sha(SOURCE/'analysis-code'/name) for name in ('audit_genome.py', 'audit_replay.py')},
            auditScripts={p.name: sha(p) for p in sorted(Path(__file__).parent.glob('audit_*.py'))},
            newSearchFE=0, newDecodes=0, seconds=time.perf_counter()-started, results=results)
        write(destination, report)
        print('REQUEST_INDEPENDENT_AUDIT_PASS', category, len(results), successful, flush=True)
    except Exception as error:
        write(destination, dict(passed=False, category=category, error=type(error).__name__+': '+str(error),
              completedRuns=len(results), results=results, newSearchFE=0, newDecodes=0, seconds=time.perf_counter()-started))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--category', choices=('engineering', 'science'), required=True)
    args = parser.parse_args()
    run_audit(args.root, args.category)
