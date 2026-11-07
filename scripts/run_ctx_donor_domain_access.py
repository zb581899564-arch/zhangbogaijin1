"""Preregistered zero-FE attribution audit of fixed-family-only initial resource support."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import re
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock, nondominated
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import resolve_class
from ctx_domain_access_data import terminal, initial_check, partition_case, pipeline_access

CONTRACT = ROOT/'research/gomea_reference_audit/CTX_DONOR_DOMAIN_ACCESS_V1.json'
FAMILY_SOURCE = ROOT/'runs/night-research-H1-20261103-010138-848045/source/src/algorithms/cooperation/FamilyContexts.java'


def sources(root, plan):
    source, pipeline = Path(plan['source']), Path(plan['pipeline'])
    identities = {}
    for base, filename, expected in ((source, 'independent-final-audit.json', plan['sourceAuditSHA256']),
                                    (pipeline, 'final-observer-audit.json', plan['pipelineAuditSHA256'])):
        assert read(base/filename)['passed'] and digest(base/filename) == expected
        identities[str(base/filename)] = expected
    cp = (source/'classpath.txt').read_text('utf-8-sig').strip()
    classes = {}
    for name in ('org.uma.jmetal.util.research.cooperation.FamilyContexts',
                 'org.uma.jmetal.util.research.search.GomWorkspace',
                 'org.uma.jmetal.util.research.modelglobal.PaMixingMove'):
        classes[name] = resolve_class(cp, name)
    expected = read(ROOT/'research/gomea_reference_audit/CTX_GOM_LOCAL_ENGINEERING_V1.json')['criticalOriginalClasses']
    family = 'org.uma.jmetal.util.research.cooperation.FamilyContexts'
    assert classes[family] == expected[family]
    execute(['E:/javavava/bin/javap.exe', '-classpath', cp, '-c', '-p', family], root/'family-bytecode.txt')
    code = (root/'family-bytecode.txt').read_text('utf-8-sig')
    body = code.split('void initialize(')[1].split('void restore(')[0]
    assert re.search(r'bipush\s+20', body) and 'iconst_5' in body and 'idiv' in body
    text = FAMILY_SOURCE.read_text('utf-8-sig')
    assert 'if (index >= 20) return;' in text and 'int family = index / 5;' in text
    identities[str(FAMILY_SOURCE)] = digest(FAMILY_SOURCE)
    for path in (source/'source/GomWorkspace.java',
                 ROOT/'runs/pa-capability-interfaces-20261105-175043-036508/source/PaMixingMove.java'):
        identities[str(path)] = digest(path)
    write_once(root/'class-identities.json', classes)
    return identities


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        plan = read(CONTRACT); before = protected()
        root = ROOT/'runs'/datetime.now().strftime('ctx-donor-domain-access-%Y%m%d-%H%M%S-%f')
        root.mkdir(); print('CTX_DONOR_DOMAIN_ACCESS_ROOT', root, flush=True)
        write_once(root/'protocol.json', dict(contract=plan, contractSHA256=digest(CONTRACT), protectedBefore=before,
            scopeNote='Saved encoding representatives only, not proof an objective vector requires these alleles; no bound on all possible schedules.'))
        identities = sources(root, plan)
        source = Path(plan['source']); old = read(source/'protocol.json')
        cases, pipeline_results, initials, targets_by_case = [], [], {}, {}
        for spec in old['instances']:
            stem, norm = spec['stem'], spec['normalization']; records = []
            for seed in old['seeds']:
                shared, ordinary = [source/stem/str(seed)/('FE500K-'+arm) for arm in ('SHARE_CTX_GOM', 'PA_JOINT')]
                initial = initial_check(shared, ordinary); targets = terminal(ordinary); peer = terminal(shared)
                initials[stem, seed] = initial; targets_by_case[stem, seed] = targets
                for folder in (shared, ordinary):
                    receipt, = rows(folder/'run-receipt.jsonl')
                    assert receipt['successful'] == receipt['attempted'] == 500000 and receipt['failed'] == 0
                    for name in ('run-receipt.jsonl', 'initial-population.jsonl', 'checkpoint-solutions.jsonl', 'anytime.jsonl'):
                        identities[str(folder/name)] = digest(folder/name)
                records.append((seed, initial, targets, peer))
            reference = nondominated(np.vstack([(np.array([p['objectives'] for p in group])-norm['lower'])/norm['scale']
                                               for _, _, targets, peer in records for group in (targets, peer)]))
            for seed, initial, targets, peer in records:
                row = partition_case(stem, seed, initial, targets, peer, norm, reference)
                row.update(normalization=norm, reference=reference.tolist())
                cases.append(row)
        for arm in ('SHARE_CTX_GOM', 'UNIFORM_CTX_GOM'):
            path = Path(plan['pipeline'])/'100_2_3_1'/(arm+'-OBSERVED')/'pipeline.jsonl'
            identities[str(path)] = digest(path)
            row = pipeline_access(path, targets_by_case['100_2_3_1', 14910003], initials['100_2_3_1', 14910003])
            pipeline_results.append(dict(arm=arm, **row))
        assert protected() == before
        initial_pass = all(c['preconditionPass'] for c in cases)
        observed_pass = all(p['preconditionPass'] for p in pipeline_results)
        result = dict(cases=cases, pipelines=pipeline_results, initialAccessPreconditionPass=initial_pass,
            observedAccessPreconditionPass=observed_pass,
            decision='STRUCTURAL_CANDIDATE_ONLY_SEPARATE_SAME_ENTRY_CONTRACT_REQUIRED' if initial_pass and observed_pass
                     else 'STOP_INITIAL_FIXED_ALLELE_ACCESS_EXPLANATION',
            newSearchFE=0, newObjectiveQueries=0, newDecoderCalls=0, newProposalConstructions=0,
            actualAlgorithmReachabilityProved=False, performanceProved=False, defaultMainlineChanged=False, goalAchieved=False)
        write_once(root/'source-identities.json', identities); write_once(root/'analysis.json', result)
        directory = root/'source'; directory.mkdir()
        for name in ('run_ctx_donor_domain_access.py', 'ctx_domain_access_data.py'):
            shutil.copy2(Path(__file__).with_name(name), directory)
        write_once(root/'source-hashes.json', {p.name: digest(p) for p in directory.iterdir()})
        write_once(root/'status.json', dict(status='COMPLETE', decision=result['decision'], goalAchieved=False))
        print('CTX_DOMAIN_ACCESS_COMPLETE', result['decision'], flush=True)
        for row in cases:
            print(row['instance'], row['seed'], row['targetFraction'], row['lostHVRelativeToPAHVPercent'], flush=True)
        for row in pipeline_results:
            print(row['arm'], row['materiallyBlockedPasses'], row['passes'], row['everFreeAlleleSupportedTargets'], row['targetCount'], flush=True)


if __name__ == '__main__':
    main()
