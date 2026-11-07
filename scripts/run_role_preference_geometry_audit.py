"""Descriptive same-candidate scalar preference overlap, conditioned on actual receiver role; zero FE."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, rows, read, write_once, controller_lock
from research.semantic_repair.evidence import digest

PA = ROOT/'runs/pa-neutral-relay-probe-20261106-033038-764322'
QPA = ROOT/'runs/qpa-complete-engineering-20261106-024925-292174'
PAIRS = ((0, 1, 'Cmax_TEC'), (0, 2, 'Cmax_TWC'), (1, 2, 'TEC_TWC'))


def summarize(counter):
    result = {'paidSteps': counter['paid'], 'allThreeUnchanged': counter['000.changed'], 'pairs': {}}
    for _, _, label in PAIRS:
        union, both = counter[label+'.unionImprove'], counter[label+'.bothImprove']
        changed = counter[label+'.eitherChanged']; opposed = counter[label+'.opposed']
        result['pairs'][label] = {'unionImprove': union, 'bothImprove': both, 'onlyFirstImproves': counter[label+'.firstOnly'],
            'onlySecondImproves': counter[label+'.secondOnly'], 'jaccardOfImprovement': both/union if union else None,
            'eitherObjectiveChanged': changed, 'strictlyOpposed': opposed, 'opposedAmongChanged': opposed/changed if changed else None}
    return result


def analyze(stem, arm, folder):
    counters = {}; steps = 0
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line)
            if event['kind'] != 'step':
                continue
            steps += 1; delta = [(-1 if a < b else 1 if a > b else 0) for a, b in zip(event['objectives'], event['parentObjectives'])]
            for group in ('ALL', event['role']):
                c = counters.setdefault(group, Counter()); c['paid'] += 1; c['000.changed'] += all(v == 0 for v in delta)
                for i, j, label in PAIRS:
                    a, b = delta[i] < 0, delta[j] < 0
                    c[label+'.unionImprove'] += a or b; c[label+'.bothImprove'] += a and b
                    c[label+'.firstOnly'] += a and not b; c[label+'.secondOnly'] += b and not a
                    c[label+'.eitherChanged'] += delta[i] != 0 or delta[j] != 0
                    c[label+'.opposed'] += delta[i]*delta[j] < 0
    receipt, = rows(folder/'receipt.jsonl'); assert receipt['successfulFE']-100 == steps and receipt['status'] == 'COMPLETE'
    return {'stem': stem, 'arm': arm, 'source': str(folder), 'groups': {k: summarize(v) for k, v in counters.items()},
            'sourceSHA256': {name: digest(folder/name) for name in ('receipt.jsonl', 'events.jsonl')}}


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        assert read(PA/'status.json')['status'] == 'COMPLETE' and read(QPA/'status.json')['engineeringPass']
        root = ROOT/'runs'/datetime.now().strftime('role-preference-geometry-%Y%m%d-%H%M%S-%f'); root.mkdir()
        shutil.copy2(Path(__file__), root/Path(__file__).name)
        write_once(root/'protocol.json', {'version': 'SAME_CANDIDATE_ROLE_GEOMETRY_DESCRIPTION-v1',
            'scope': 'All already-paid first-two-generation proposals, compare three exact scalar improvement predicates on the same child/parent; stratify actual role. No new targets or algorithm changes',
            'interpretation': 'Descriptive off-policy preference overlap, not causal four-role efficacy, fatigue-specific evidence or justification to rename roles. No thresholds or performance gate',
            'newSearchFE': 0, 'decoderCalls': 0, 'goalAchieved': False})
        results = []
        for stem in ('20_8_5_1', '100_2_3_1'):
            for arm in ('STRICT', 'EQUAL'):
                results.append(analyze(stem, arm, PA/stem/arm))
            results.append(analyze(stem, 'QPA', QPA/stem/'main'))
        write_once(root/'analysis.json', {'instances': results, 'previouslyPaidStepsRead': sum(r['groups']['ALL']['paidSteps'] for r in results),
            'newSearchFE': 0, 'decoderCalls': 0, 'defaultMainlineChanged': False, 'goalAchieved': False})
        write_once(root/'status.json', {'status': 'COMPLETE', 'newSearchFE': 0, 'decoderCalls': 0, 'goalAchieved': False})
        print('ROLE_PREFERENCE_GEOMETRY_COMPLETE', root,
              [(r['stem'], r['arm'], r['groups']['ALL']['pairs']['TEC_TWC']) for r in results], flush=True)


if __name__ == '__main__':
    main()
