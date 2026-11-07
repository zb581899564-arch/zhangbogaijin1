"""Zero-decoder audit of actual VNS exits; acceptance disagreement is not a continuation result."""
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock, hypervolume
from research.semantic_repair.evidence import digest
from fa_admission_volume import volume, checks

SOURCE = ROOT / 'runs/local-program-audit-20261105-123427-539293'
STEMS = ('20_8_5_1', '100_2_3_1')
METHODS = ('FULL', 'NSGA')
REFERENCES = (1.25, 1.5, 2.)
TOLERANCE = 1e-10


def protocol():
    return {'source': str(SOURCE), 'searchFE': 0, 'decoderCalls': 0,
        'question': 'Do actual CENTER VNS exits with new archive value get rejected by PDDR often '
                    'enough to justify a separate indicator-acceptance continuation probe?',
        'scope': 'Existing4original-kernel100k trajectories,2developmentinstances,oldseed12390003. '
                 'Allcompleted CENTER programs included; partial and other roles retained as separate counts. '
                 'No replay, new candidate, altered acceptance, reference source, operator or teacher.',
        'engineering': 'Independently reconstruct every actual CENTER PDDR decision from paid reference '
                       'objectives and both endpoints; duplicates retained. Verify reference availableAtPaidFE '
                       'and each reference point physical paid birth<=program start. Any disagreement stops '
                       'engineering. Source annotations and previous independent archive check remain required.',
        'counterfactual': 'Compare single endpoint contributions against SAME frozen100-point reference '
                          'at1.25,1.5,2.0 and original normalization. Strictly prefer candidate when its '
                          'reference-set HV exceeds incumbent by>1e-10. This is only a decision on old '
                          'candidate pairs, not the resulting policy trajectory or measured advantage.',
        'archiveValue': 'Reuse previously independently rebuilt pre-program archive endpointSingleHVgain. '
                        'Only gains>1e-10 count. A newly accepted endpoint is informative only if it was '
                        'actually rejected, adds value against pre-program paid archive, and counterfactual '
                        'HV would accept it. Sum of conditional endpoint gains is not a unionHV or a causal gain.',
        'gate': 'BOTH FULL instances: at least100completeCENTER programs; at least20 actual-rejected '
                'new-valued endpoints accepted by HV atALL3references; their summed conditional gains '
                '>=10% of all positive CENTER endpoint gains and>=1% of all completed original program '
                'sequentialHVgain. Only this permits a separate matched FULL/NSGA continuation protocol. '
                'Matched NSGA opportunity reported; no four-role attribution from disagreement alone.',
        'stop': 'If capacity fails, do not switch CENTER acceptance, add a learner, choose another reference '
                'point, select a role/window subset or run variants to rescue. Missing data not converted '
                'to negative scientific evidence. Prior identity-shake5% hypothesis remains stopped.',
        'invariants': 'Four responsibilities, QGS, protected FA families, sharing, decoder, budgets and '
                      'production unchanged. No download, upload, remote task or same-time performance claim.'}


def dominates(point, others):
    return np.all(point <= others, axis=1) & np.any(point < others, axis=1)


def pddr(candidate, incumbent, reference):
    p_c = int(np.sum(dominates(candidate, reference)))
    q_c = int(np.sum(dominates(reference, candidate)))
    p_i = int(np.sum(dominates(incumbent, reference)))
    q_i = int(np.sum(dominates(reference, incumbent)))
    c_i = bool(np.all(candidate <= incumbent) and np.any(candidate < incumbent))
    i_c = bool(np.all(incumbent <= candidate) and np.any(incumbent < candidate))
    c = q_c + int(i_c) + 1. / (p_c + int(c_i) + 1)
    i = q_i + int(c_i) + 1. / (p_i + int(i_c) + 1)
    return c, i


def reference_scores(program, references, scale, cache):
    reference = references[program['reference']]
    raw = np.asarray([p['objectives'] for p in reference['points']])
    candidate, incumbent = np.asarray(program['improved']), np.asarray(program['entry'])
    c, i = pddr(candidate, incumbent, raw)
    assert (c < i) == program['accepted'], f'Actual CENTER acceptance mismatch at {program["episode"]}'
    assert reference['availableAtPaidFE'] <= program['startFE']
    assert all(p['earliestEquivalentPhysicalPaidFE'] <= program['startFE'] for p in reference['points'])
    normalized = (raw - scale['lower']) / scale['scale'];scores = {}
    for ref in REFERENCES:
        values = []
        for point in (candidate, incumbent):
            key = program['reference'], ref, tuple(point)
            if key not in cache:
                scaled = (point - scale['lower']) / scale['scale']
                cache[key] = volume(np.vstack([normalized, scaled]), (ref,) * 3)
            values.append(cache[key])
        scores[str(ref)] = {'candidateReferenceHV': values[0], 'incumbentReferenceHV': values[1],
            'wouldAccept': values[0] > values[1] + TOLERANCE}
    return c, i, scores


def summarize(programs, evidence):
    new = [p for p in evidence if p['endpointSingleHVgain'] > TOLERANCE]
    rejected = [p for p in new if not p['accepted']]
    blocked = [p for p in rejected if all(p['hvDecisions'][str(ref)]['wouldAccept'] for ref in REFERENCES)]
    new_gain = sum(p['endpointSingleHVgain'] for p in new)
    blocked_gain = sum(p['endpointSingleHVgain'] for p in blocked)
    program_gain = sum(p['totalHVgain'] for p in programs if p['completed'])
    return {'completedCenterPrograms': len(evidence), 'allCompletedPrograms': sum(p['completed'] for p in programs),
        'partialPrograms': sum(not p['completed'] for p in programs),
        'positiveCenterEndpoints': len(new), 'rejectedPositiveCenterEndpoints': len(rejected),
        'rejectedValuableAndHVAcceptAllReferences': len(blocked),
        'allPositiveCenterEndpointConditionalGainSum': new_gain, 'blockedEndpointConditionalGainSum': blocked_gain,
        'blockedShareOfPositiveCenterEndpointGains': blocked_gain / new_gain if new_gain > TOLERANCE else None,
        'allProgramSequentialHVgain': program_gain,
        'blockedConditionalGainOverAllProgramSequentialGain': blocked_gain / program_gain if program_gain > TOLERANCE else None,
        'pddrTies': sum(p['candidatePddr'] == p['incumbentPddr'] for p in evidence),
        'hvDecisionDisagreements': {str(ref): sum(p['hvDecisions'][str(ref)]['wouldAccept'] != p['accepted'] for p in evidence)
                                   for ref in REFERENCES},
        'gate': len(evidence) >= 100 and len(blocked) >= 20 and new_gain > TOLERANCE and program_gain > TOLERANCE
                and blocked_gain >= .1 * new_gain and blocked_gain >= .01 * program_gain}


def audit_one(root, spec, method):
    old = SOURCE / spec['stem'] / method;out = root / spec['stem'] / method;out.mkdir(parents=True)
    programs = read(old / 'program-value-rows.json');references = {r['id']: r for r in rows(old / 'program-references.jsonl')}
    acceptance = read(old / 'program-value-analysis.json')['independentArchiveAndFEAcceptance']
    receipt, = rows(old / 'run-receipt.jsonl')
    assert acceptance['paidRows'] == receipt['successful'] == 100000
    assert 100000 in acceptance['checkedFEFronts'] and acceptance['maxIndependentHVError'] < 1e-11
    raw = {p['episode']: p for p in rows(old / 'local-programs.jsonl')}
    evidence, cache = [], {}
    for p in programs:
        assert all(p[k] == value for k, value in raw[p['episode']].items())
        if not p['completed'] or p['preference'] != 'CENTER': continue
        c, i, scores = reference_scores(p, references, spec['normalization'], cache)
        evidence.append({**p, 'candidatePddr': c, 'incumbentPddr': i, 'hvDecisions': scores})
    result = {'stem': spec['stem'], 'method': method, **summarize(programs, evidence)}
    write_once(out / 'analysis.json', {**result, 'programs': evidence})
    print('PROGRAM_ACCEPTANCE_AUDIT', result, flush=True)
    return result


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        root = ROOT / 'runs' / datetime.now().strftime('program-acceptance-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PROGRAM_ACCEPTANCE_AUDIT_ROOT', root, flush=True)
        results = []
        try:
            assert read(SOURCE / 'status.json')['status'] == 'COMPLETE'
            write_once(root / 'protocol.json', protocol());shutil.copy2(Path(__file__), root / Path(__file__).name)
            write_once(root / 'numeric-hv-checks.json', checks(hypervolume))
            specs = read(SOURCE / 'protocol.json')['instances']
            assert {s['stem'] for s in specs} == set(STEMS)
            selected = [SOURCE / stem / method / filename for stem in STEMS for method in METHODS
                for filename in ('program-value-rows.json', 'program-references.jsonl', 'local-programs.jsonl',
                                 'program-value-analysis.json', 'run-receipt.jsonl', 'loaded-identity.json')]
            write_once(root / 'input-hashes.json', {str(p.relative_to(SOURCE)): digest(p) for p in selected})
            write_once(root / 'source-hashes.json', {Path(__file__).name: digest(Path(__file__)),
                'fa_admission_volume.py': digest(Path(__file__).with_name('fa_admission_volume.py'))})
            for spec in specs:
                for method in METHODS: results.append(audit_one(root, spec, method))
            worthwhile = all(r['gate'] for r in results if r['method'] == 'FULL')
            write_once(root / 'analysis.json', {'trajectories': results, 'worthMatchedIndicatorContinuation': worthwhile,
                'additionalSearchFE': 0, 'additionalDecoderCalls': 0, 'goalAchieved': False})
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'completed': results,
                'additionalSearchFE': 0, 'additionalDecoderCalls': 0});raise
        write_once(root / 'status.json', {'status': 'COMPLETE', 'additionalSearchFE': 0, 'additionalDecoderCalls': 0,
            'worthMatchedIndicatorContinuation': worthwhile, 'goalAchieved': False})


if __name__ == '__main__': main()
