"""Reconstruct original inner descent from paid objectives; no genotype or continuation claim."""
import csv
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from research.semantic_repair.evidence import digest
from local_program_stream import PaidArchiveStream
from run_program_acceptance_audit import pddr

SOURCE = ROOT / 'runs/local-program-audit-20261105-123427-539293'
TOLERANCE = 1e-10


def protocol():
    return {'source': str(SOURCE), 'additionalSearchFE': 0, 'decoderCalls': 0,
        'question': 'Do original CENTER descents discover substantial new nondominated objective states '
                    'that are rejected and never used as a descent parent within that same program?',
        'reconstruction': 'Use ALL4original100k trajectories, oldseed12390003, all complete programs and '
                          'separate partial tails. Start inner descent at paid SHAKE, independently reproduce '
                          'each strict makespan/PDDR comparison and update. Final current must exactly equal '
                          'recorded improved endpoint for every complete program. Rebuild entire paid archive '
                          'and every registered FE front using original independent stream.',
        'witness': 'DESCENT candidate rejected by original comparison, with actual new archive admission '
                   'and sequential HV gain>1e-10 at birth; for CENTER require candidate/current mutually '
                   'nondominated. Track all later same-program parent objective values, report whether '
                   'rejected state objective was ever expanded. This is objective-state evidence only: '
                   'no complete genome available for all children, no assertion about other programs or '
                   'future generations, and no causal continuation gain inferred from discovery.',
        'gate': 'BOTH FULL instances must have>=20completeCENTER programs with>=1unexpanded witness, '
                'cover>=10% of completeCENTER programs, and witness sequentialHVgain>=10% of all '
                'completeCENTER descent sequentialHVgain. This only permits isolated whole-genome '
                'capture and a separate matched continuation protocol, not a queue/policy implementation. '
                'Report matched NSGA evidence; no four-role credit from capacity alone.',
        'boundaries': 'Old outer-HV rule remains stopped; no moving it into inner descent, changing '
                      'reference/normalization/threshold, promoting a control, or tuning budget/parent order. '
                      'Possible different future question is multi-state continuation, not another scalar '
                      'exit score. Generic Pareto local search is not a new contribution by itself.',
        'limits': 'Witness volume was ALREADY in result archive. Expanding a witness may improve or worsen '
                  'future performance; this audit does not evaluate that. Model, four roles, QGS, families, '
                  'sharing, neighborhoods, default mainline and all previous stopping decisions unchanged. '
                  'No transfer or additional runtime experiment.'}


def finish_program(program, current, events, parents):
    if program['completed']:
        assert np.array_equal(current, np.asarray(program['improved'])), 'Reconstructed inner endpoint differs'
    for event in events:
        event['usedAsLaterParentWithinProgram'] = tuple(event['candidate']) in parents
        event['completeProgram'] = program['completed']
    return {'episode': program['episode'], 'completed': program['completed'], 'preference': program['preference'],
        'rejectedNewStates': len(events), 'unexpandedWitnesses': sum(not e['usedAsLaterParentWithinProgram'] for e in events),
        'unexpandedWitnessSequentialGain': sum(e['sequentialHVgain'] for e in events if not e['usedAsLaterParentWithinProgram']),
        'descentSequentialGain': program['descentHVgain']}


def analyze(root, spec, method):
    old = SOURCE / spec['stem'] / method;out = root / spec['stem'] / method;out.mkdir(parents=True)
    programs = {p['episode']: p for p in read(old / 'program-value-rows.json')}
    references = {r['id']: np.asarray([p['objectives'] for p in r['points']]) for r in rows(old / 'program-references.jsonl')}
    stream = PaidArchiveStream(old, spec['normalization'])
    active = None;current = None;events = [];parents = set();summaries = [];witnesses = [];decisions = 0
    with (old / 'program-paid-objectives.csv').open(encoding='utf-8') as source:
        for row in csv.DictReader(source):
            fe, episode = int(row['fe']), int(row['episode']);point = np.asarray([float(row[k]) for k in ('C', 'E', 'W')])
            before = stream.hv
            if episode == 0:
                assert active is None;stream.advance(fe);continue
            program = programs[episode]
            if row['phase'] == 'SHAKE':
                assert active is None and fe == program['startFE'] + 1
                active = episode;current = point.copy();events = [];parents = set()
            else:
                assert row['phase'] == 'DESCENT' and active == episode
                parent = current.copy();parents.add(tuple(parent));decisions += 1
                if program['preference'] == 'CENTER':
                    candidate_score, parent_score = pddr(point, parent, references[program['reference']])
                    accepted = candidate_score < parent_score
                else:
                    assert program['preference'] == 'MAKESPAN';accepted = point[0] < parent[0]
                if accepted: current = point.copy()
            after = stream.advance(fe, episode, row['phase'])
            if row['phase'] == 'DESCENT' and not accepted and bool(int(row['archiveChanged'])) and after - before > TOLERANCE:
                if program['preference'] == 'CENTER':
                    assert np.any(point < parent) and np.any(point > parent), 'Rejected CENTER admission not a genuine tradeoff'
                event = {'episode': episode, 'fe': fe, 'candidate': point.tolist(), 'parent': parent.tolist(),
                    'preference': program['preference'], 'reference': program['reference'], 'sequentialHVgain': after - before}
                events.append(event);witnesses.append(event)
            if fe == program['endFE']:
                summaries.append(finish_program(program, current, events, parents));active = None
    independent = stream.finish(100000)
    assert active is None and {p['episode'] for p in summaries} == {p['episode'] for p in programs.values() if p['endFE'] > p['startFE']}
    center = [p for p in summaries if p['completed'] and p['preference'] == 'CENTER']
    covered = sum(p['unexpandedWitnesses'] > 0 for p in center)
    gain = sum(p['unexpandedWitnessSequentialGain'] for p in center);all_gain = sum(p['descentSequentialGain'] for p in center)
    result = {'stem': spec['stem'], 'method': method, 'independentInnerComparisons': decisions,
        'completeCenterPrograms': len(center), 'centerProgramsWithUnexpandedWitness': covered,
        'centerProgramCoverage': covered / len(center) if center else None,
        'unexpandedCenterWitnesses': sum(p['unexpandedWitnesses'] for p in center),
        'unexpandedCenterWitnessSequentialGain': gain, 'allCompleteCenterDescentSequentialGain': all_gain,
        'witnessShareOfCenterDescentGain': gain / all_gain if all_gain > TOLERANCE else None,
        'gate': covered >= 20 and covered >= .1 * len(center) and all_gain > TOLERANCE and gain >= .1 * all_gain,
        'independentPaidArchiveAcceptance': independent}
    write_once(out / 'analysis.json', {**result, 'programs': summaries, 'witnesses': witnesses})
    print('PRUNED_PROGRAM_STATES', result, flush=True)
    return result


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        assert read(SOURCE / 'status.json')['status'] == 'COMPLETE'
        root = ROOT / 'runs' / datetime.now().strftime('pruned-program-states-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PRUNED_PROGRAM_STATES_ROOT', root, flush=True);results = []
        write_once(root / 'protocol.json', protocol());shutil.copy2(Path(__file__), root)
        try:
            specs = read(SOURCE / 'protocol.json')['instances']
            inputs = [SOURCE / spec['stem'] / method / name for spec in specs for method in ('FULL', 'NSGA')
                      for name in ('program-value-rows.json', 'program-references.jsonl', 'program-paid-objectives.csv', 'anytime.jsonl')]
            write_once(root / 'input-hashes.json', {str(p.relative_to(SOURCE)): digest(p) for p in inputs})
            for spec in specs:
                for method in ('FULL', 'NSGA'):results.append(analyze(root, spec, method))
            worth_capture = all(r['gate'] for r in results if r['method'] == 'FULL')
            write_once(root / 'analysis.json', {'trajectories': results, 'worthWholeGenomeWitnessCapture': worth_capture,
                'searchQueueImplemented': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'completed': results,
                'additionalSearchFE': 0, 'decoderCalls': 0});raise
        write_once(root / 'status.json', {'status': 'COMPLETE', 'additionalSearchFE': 0, 'decoderCalls': 0,
            'worthWholeGenomeWitnessCapture': worth_capture, 'goalAchieved': False})


if __name__ == '__main__': main()
