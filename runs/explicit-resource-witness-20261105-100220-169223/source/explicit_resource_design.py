"""Frozen representation-coverage test, with no online algorithm or new selector."""
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once

SOURCE = ROOT / 'runs/natural-regime-bench-20261105-073626-086353'
KERNEL = ROOT / 'runs/action-feedback-probe-20261105-094303-818797'
STEMS = ('20_8_5_1', '100_2_3_1')
CHECKPOINTS = (5100, 500000)
ORIGINS = ('FULL_NAT', 'NSGA_NAT')


def design():
    return {
        'source': str(SOURCE), 'kernel': str(KERNEL),
        'instances': read(SOURCE / 'protocol.json')['instances'],
        'sourceSeed': 12390003, 'initializationSeed': 12920003,
        'hypothesis': 'A later-stage explicit machine/worker decision can express useful feasible '
                      'schedules unavailable while preserving the same old four vectors/first-stage timeline. '
                      'This does not explain why same-encoding NSGA beats FULL or prove four-role advantage.',
        'policy': 'Separate explicit-resource-append-v1. Same physical formulas, factory/job precedence, '
                  'stage-local exclusive resources, stable completion-order FIFO and earliest start given selected '
                  'resources. Default later decisions use original FAM. No active wait, gap insertion, shift or new target.',
        'identity': 'Immutable StageResourcePlan and distinct ExplicitSchedule/cache key. '
                    'No reuse of dynamic.schedule, no result cached by four old vectors alone. '
                    'All prototype calls perform full recomputation; production decoder/validator untouched.',
        'sampling': 'Both original natural FULL and NSGA paid checkpoint fronts, FE5100 and500000, each '
                    'sorted lexicographically by all four vectors;16equally spaced indexes floor(i*(n-1)/15). '
                    'Keep all duplicates and source labels, no replacements.64parents per instance,128total. '
                    'Selected job position=parentOrdinal%N; later stage=1+parentOrdinal%(S-1).',
        'candidates': 'FIRST: all other first-stage machine/worker pairs for the same selected job, '
                      'without changing JS/FA. LATER: all other resource pairs at the one selected later operation, '
                      'original four vectors and first-stage timeline fixed. Each candidate independent from parent. '
                      'Different physical resource counts are retained, not hidden; best coverage is an oracle, '
                      'uniform mean is one-candidate expectation. No free preview/selection in search.',
        'budget': 'Exact planned paidFE computed from resource counts before any witness decode: '
                  'sum_parent[1+(M_f0*W_f0-1)+(M_fk*W_fk-1)]. Hard cap10000perinstance,20000total. '
                  'Every parent, duplicate and candidate paid through RunContext; no source searches. '
                  'Engineering separately10successfulFE+2deliberate failed attempts,384offline full decodes.',
        'engineering': 'Every128selected parent: old full, explicit empty, explicit same-original-binding '
                       'full timelines/objectives bit-exact, independently validated. Plan identity/immutability. '
                       'Per instance FE1/2/3fixtures: last acquired decode completes, different explicit binding '
                       'passes independent physics but is rejected by unmodified old validator; bad range rejects '
                       'before decode at3rd attemptedFE with2success+1failure and real last valid archive. '
                       'Do not start witness if any engineering check fails.',
        'witnessQA': 'All paid schedules independently audit full physical timeline. FIRST/parents additionally '
                     'match old full decoder bit-exact; LATER preserve all original vectors/first-stage timeline '
                     'and are explicitly rejected by old binding-policy validator. QA work separately counted. '
                     'Log paidFE1,2,last, every outcome, failed attempt, last valid archive and full first-candidate timelines.',
        'background': 'For each instance and paid sourceFE, union of both original source fronts at that exact '
                      'checkpoint, no future front. Same background for both origins and channels. '
                      'Normalization copied from source; refs1.5primary,1.25and2sensitivity.',
        'gate': 'Both instances required:>=13/64parents where best later SINGLE candidate adds>=0.1%of '
                'common background HV; at least one such witness in each of four(origin,checkpoint)cells; '
                'mean later oracle single gain>=1.10*first-stage oracle gain, nonzero first control required; '
                'mean uniform later single gain>=uniform first gain; each checkpoint later oracle mean>=first; '
                'refs1.25/2 aggregate later oracle gain>=first. Median paired case mean formation+guarded '
                'evaluation cost ratio<=1.25 when both channels exist. All necessary. '
                'Failure stops this fixed one-operation extension route without stage/job/resource/threshold/seed scans.',
        'nextIfPass': 'Only separately preregister a controllable full representation/search with identical '
                      'extended representation, repair, decoder/local budget available to strong NSGA. '
                      'Retain four-role/share ablations and original shared/Li controls; full sameFE/time '
                      'and fresh instances/seeds are still required before independent confirmation.',
        'limits': 'Coverage oracle and one-candidate expectation, not full algorithm dominance or a free action '
                  'selector, learned policy, dynamic-fatigue-specific mechanism, independent confirmation '
                  'or new publication contribution. No mainline, role/Q/shared rule change, download or external transfer.'
    }


def genome_key(point):
    return tuple(tuple(point[key]) for key in ('JS', 'FA', 'MA', 'WA'))


def prepare(root, stem):
    shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')
    fronts, selected, lines = {}, [], []
    for origin in ORIGINS:
        records = rows(SOURCE / stem / ('FE-' + origin) / 'checkpoint-solutions.jsonl')
        for checkpoint in CHECKPOINTS:
            points = [p for p in records if p['checkpointKind'] == 'FE' and p['checkpoint'] == checkpoint]
            assert len(points) >= 16
            assert all(p['bornFE'] <= p['checkpointFE'] == checkpoint for p in points)
            points.sort(key=genome_key)
            fronts[f'{origin}:{checkpoint}'] = points
            for index in range(16):
                parent = points[index * (len(points) - 1) // 15]
                ordinal = len(selected)
                position, stage = ordinal % len(parent['JS']), 1 + ordinal % (int(stem.split('_')[1]) - 1)
                item = {'id': f'p{ordinal}', 'origin': origin, 'sourceFE': checkpoint, 'index': index,
                        'position': position, 'stage': stage, 'parent': parent}
                selected.append(item)
                fields = [item['id'], origin, str(checkpoint), str(index), str(position), str(stage)]
                fields += [','.join(map(str, parent[key])) for key in ('objectives', 'JS', 'FA', 'MA', 'WA')]
                lines.append('\t'.join(fields))
    assert len(selected) == 64
    write_once(root / stem / 'source-fronts.json', fronts)
    write_once(root / stem / 'selected.json', selected)
    (root / stem / 'cases.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
