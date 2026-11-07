"""Final independent ancestry/source accounting, using the already checked full step/timeline traces."""
from collections import Counter
from pathlib import Path
import json
import shutil
import sys

from run_long_budget_bridge import ROOT, read, rows, write_once
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture, resolve_class
from ctx_gom_replay import raw_hash
from ctx_gom_engineering_cases import fees
from ctx_fork_engineering_support import native_folder


def check_entry_records(folder, receipt, fork):
    paid = {}
    with (folder/'gom-events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['kind'] == 'paid':
                paid.setdefault(row['rawHash'], row['fe'])
    for event in fork['entries']:
        for cohort in ('before', 'global', 'local'):
            points = event[cohort]
            assert len(points) == 100
            assert Counter(p['family'] for p in points) == Counter({-1:80,0:5,1:5,2:5,3:5})
            assert Counter(p['direction'] for p in points) == Counter(MAKESPAN=15,CENTER=55,ENERGY=15,WORKER_COST=15)
            for point in points:
                assert raw_hash(point) == point['rawSHA256'] and point['rawSHA256'] in paid
                assert paid[point['rawSHA256']] <= receipt['successful']
                if event['cycle'] == 1:
                    assert paid[point['rawSHA256']] <= (100 if cohort == 'before' or cohort == 'local' and event['source'] == 'PRE' else 5100)
        expected = event['before'] if event['source'] == 'PRE' else event['global']
        assert event['local'] == expected
        assert event['source'] == ('PRE' if fork['mode'] == 'PRE_FIRST' and event['cycle'] == 1 else 'POST')
    return sum(len(e[c]) for e in fork['entries'] for c in ('before','global','local'))


def audit(root):
    protocol = read(root/'protocol.json'); plan = protocol['contract']
    assert read(root/'status.json')['engineeringPass'] and read(root/'acceptance.json')['passed']
    assert protected() == protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/CTX_FIRST_LOCAL_FORK_ENGINEERING_V1.json') == protocol['contractSHA256']
    assert class_hashes(root/'classes') == read(root/'class-hashes.json')
    for name, sha in read(root/'source-hashes.json').items():
        assert digest(root/'source'/name) == sha
    original = read(root/'original-canonical-source.json')
    assert digest(Path(original['path'])) == original['sha256']
    cp = (root/'classpath.txt').read_text('utf-8-sig').strip()
    for name, value in read(root/'inherited-identities.json').items():
        assert resolve_class(cp, name) == value
    initial = {}; masters = {}; checks = []; points_checked = 0
    for spec in plan['cases']:
        stem = spec['stem']
        for name, sha in read(root/stem/'input-hashes.json').items():
            assert digest(root/stem/'inputs'/name) == sha
            assert digest(Path(plan['source'])/stem/'inputs'/name) == sha
        for folder in (root/stem).iterdir():
            if not (folder/'receipt.jsonl').exists():
                continue
            receipt, = rows(folder/'receipt.jsonl')
            assert receipt['successful'] == receipt['attempted'] == receipt['decoder']['dynamic.evaluations']
            assert receipt['failed'] == receipt['timeInterruptedAttempts'] == 0
            replay = read(folder/'independent-replay.json')
            assert replay['passed'] and receipt['paidFullTimelineQA'] == receipt['successful']
            assert read(folder/'checkpoint-validation.json')['allReachedPointsCovered']
            loaded, = rows(folder/'loaded-identity.jsonl'); verify_capture(loaded, cp)
            helper = read(folder/'fork-input.json'); verify_capture(helper['identity'], cp)
            fork = helper['fork']; points_checked += check_entry_records(folder, receipt, fork)
            if not folder.name.startswith('cut'):
                arm, mode = folder.name.rsplit('-', 1)
                masters[stem, arm, mode] = receipt
                assert receipt['gom']['completePasses'] == 2 and receipt['gom']['completePrograms'] == 200
                assert receipt['successful'] == spec['masterFE']
                assert fork['snapshotChecks'] == (100 if mode == 'PRE_FIRST' else 0)
                assert [e['source'] for e in fork['entries']] == (['PRE','POST'] if mode == 'PRE_FIRST' else ['POST','POST'])
                if mode == 'POST':
                    native, = rows(native_folder(plan, stem, arm)/'receipt.jsonl')
                    assert receipt['paidSHA256'] == native['paidSHA256']
                    assert {tuple(p['objectives']) for p in receipt['lastValidFront']} == {tuple(p['objectives']) for p in native['lastValidFront']}
                else:
                    post = read(root/stem/(arm+'-POST')/'fork-input.json')['fork']
                    assert fork['entries'][0]['before'] == post['entries'][0]['before']
                    assert fork['entries'][0]['global'] == post['entries'][0]['global']
            for p in rows(folder/'initial-population.jsonl'):
                if p['fe'] not in initial:
                    initial[p['fe']] = p
            checks.append(dict(instance=stem, case=folder.name, actualFE=receipt['successful'], stepTraceAndTimelinePassed=True))
        for arm in ('SHARE_CTX_GOM','UNIFORM_CTX_GOM'):
            assert masters[stem,arm,'POST']['paidPrefixes']['5100'] == masters[stem,arm,'PRE_FIRST']['paidPrefixes']['5100']
        for limit in spec['cutoffs']:
            row, = rows(root/stem/('cut'+str(limit))/'receipt.jsonl')
            assert row['successful'] == limit
            assert row['paidSHA256'] == masters[stem,'SHARE_CTX_GOM','PRE_FIRST']['paidPrefixes'][str(limit)]
    actual = fees(root)
    assert actual['receiptCount'] == 20 and len(checks) == 20
    assert actual['attemptedFE'] == actual['successfulFE'] == plan['plannedFixedAttemptedFE'] <= plan['maximumActualAttemptedFE']
    assert actual['failedFE'] == actual['timeInterruptedAttempts'] == 0
    record = dict(passed=True, checks=checks, **actual, independentlyCheckedAncestryRecords=points_checked,
        nativePOSTAndCommonFirst5100Proved=True, allCutoffPrefixesVerified=True,
        usesExistingAllStepAndFullTimelineChecks=True, performanceProved=False, newSearchFE=0, newDecoderCalls=0, goalAchieved=False)
    write_once(root/'independent-final-audit.json', record)
    directory = root/'independent-audit-source'; directory.mkdir(); shutil.copy2(Path(__file__), directory)
    print('CTX_FIRST_LOCAL_FORK_FINAL_AUDIT_PASS', actual, flush=True)


if __name__ == '__main__':
    audit(Path(sys.argv[1]).resolve())
