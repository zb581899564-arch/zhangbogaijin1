"""Prospective guide-source experiment; no pool selector is installed in an optimizer."""
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once

SOURCE = ROOT / 'runs/paid-archive-capture-20261105-101720-096912'
SPECS = ROOT / 'runs/mating-pool-probe-20261105-062648-478040'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)
PROBE_SEED = 12990003
METHODS = ('PAID_ND', 'HISTORY_ND', 'CURRENT_ND', 'INITIAL_ND', 'RANDOM_KNOWN')


def protocol():
    return {
        'source': str(SOURCE), 'sourceSeeds': SEEDS, 'probeSeed': PROBE_SEED,
        'engineeringInputAmendment': 'First103618preparation stopped before compilation/FE: '
                                     'current-only non-ND genotypes have paid birth but no first producing '
                                     'role saved by the old observer. Retain all, mark UNKNOWN_CURRENT_ONLY. '
                                     'No pool, source, sampling, seed or gate change; failed directory retained.',
        'instances': read(SPECS / 'protocol.json')['instances'], 'methods': METHODS,
        'question': 'Does the extra paid-archive genotype supply create useful NEW offspring with '
                    'the unchanged job-aligned kernel, beyond complete pooled accepted histories/current/initial or random known sources?',
        'sampling': 'All six original first-generation CENTER windows per instance (step0/24/49, both '
                    'source seeds). Eight equally spaced freeCENTER recipients among47; retain their '
                    'actual oldest personal ND guide by full owner index. No outcome/window/parent replacement.',
        'sources': {'PAID_ND': 'Actual all-paid archive at request; already ND and objective-deduplicated.',
                    'HISTORY_ND': 'ND of full100initial+100current+all current personal histories.',
                    'CURRENT_ND': 'ND of full100current.', 'INITIAL_ND': 'ND of full100initial.',
                    'RANDOM_KNOWN': 'Uniform over all known encoded inputs from those sources; '
                                    'not a sample of all previously attempted candidates, which were not all saved.'},
        'ndTies': 'Chronological first paid occurrence, then full encoding. One genotype for equal '
                  'objective vector within ND construction; exact source/genome duplicates merged in common '
                  'input reconstruction, membership/provenance retained. No offspring deduplication before payment.',
        'kernel': 'Actual frozen KernelVariants.JOB_ALIGNED, native six independent paper resource '
                  'triggers and repairs; unchanged config, parent and actual personal guide. Only global '
                  'guide source varies. No candidate acceptance/local search/Q update or mainline modification.',
        'randomness': 'Each recipient/rep gets one uniform quantile from an independent selector RNG '
                      'shared across source methods. Kernel RNG reset to identical starting seed after '
                      'selection. Different guide/resource/repair paths need not consume subsequent draws identically.',
        'budget': 'Common unique encoded source inputs per context replayed through RunContext once '
                  'and charged, including across-context repeats; then6contexts*8parents*16draws*5methods='
                  '3840charged offspring per instance,7680total. All paid inputs/offspring also full-timeline '
                  'QA separately. Exact setup+totalFE frozen after deterministic input preparation, before decoding.',
        'comparison': 'Equal128offspring per source per context on fixed parents/pbest. Shared paid source '
                      'reconstruction is data-generation cost, not five independently executed full optimizers. '
                      'This is not complete-algorithm sameFE/time evidence.',
        'cost': 'Record every source reconstruction/evaluation and QA separately. Pool construction '
                'for current/history/paid/random perrep amortized over exactly8children. INITIAL_ND cached '
                'once per context, cost divided by128actual children. Measure guide draw/copy, generation, '
                'repair and guarded evaluation. These are necessary frozen-pool costs; live archive '
                'snapshot/cache API, maintenance and closed-loop timing remain unvalidated.',
        'scoring': 'Single-candidate HV increase against the complete actual pre-request paid archive. '
                   'All teacher/personal/parent points must score zero extra HV. Average16draws per '
                   'recipient,48recipient-context clusters per instance. Never union all16children '
                   'and call that one candidate. Normalization/source fixed; ref1.5primary,1.25/2sensitivity.',
        'gate': 'Each instance>=24of48informative recipient clusters. PAID_ND mean single gain>=10% '
                'overHISTORY_ND andINITIAL_ND,>=5%overCURRENT_ND andRANDOM_KNOWN. >=27of48strict '
                'recipient wins vsHISTORY_ND andRANDOM_KNOWN. Each source-seed aggregate positive '
                'vsboth; each step aggregate nonnegative vsHISTORY_ND; ref1.25/2 directions vsboth '
                'positive. Median necessary per-child pool+draw/copy+kernel+evaluation cost ratio<=1.25 '
                'vsHISTORY_ND andINITIAL_ND. Zero controls inconclusive. All necessary. Failure '
                'stops this fixed source rule, without teacher rank/pool subset/seed/window/kernel tuning.',
        'engineering': 'Actual classes/JDK/SHA frozen. Every imported source paid no later than request; '
                       'full source objective replay bit-exact. Every paid offspring complete timeline '
                       'matches independent full decoder. Source vectors/objectives unchanged. Pool membership '
                       'and ND objective sets independently recomputed, complete paidFE ledger1..last; '
                       'failures retain fee receipts and last valid front.',
        'nextIfPass': 'Only a fresh protocol for native archive-read costs and closed loop, including '
                      'uniform duties and strong classical all-paid-guide feedback. Extra supply mostly '
                      'MAKESPAN at these windows cannot establish four-role unique cooperation.',
        'limits': 'Reused development sources and conditional single-offspring mechanism; no novel archive '
                  'method, full algorithm superiority, fatigue specificity, same-time gain, independent '
                  'confirmation or Li author-result reproduction. Original four roles/QGS/families/shared '
                  'rules and default decoder untouched. No downloads, transfers or public push.'
    }


def key(point):
    return tuple(tuple(point[name]) for name in ('JS', 'FA', 'MA', 'WA', 'objectives'))


def prepare(root, stem):
    shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')
    contexts, guide_lines, recipient_lines = [], [], []
    for seed in SEEDS:
        folder = SOURCE / stem / str(seed) / 'capture'
        assert read(folder / 'observation-equivalence.json')['status'] == 'PASS'
        command = read(folder / 'command.json')
        assert '-Dresearch.personal.mode=OLDEST' in command
        initial = rows(folder / 'mating-initial-points.jsonl')
        snapshots = rows(folder / 'mating-source-pools.jsonl')
        for snapshot in snapshots:
            context_id = f'c{len(contexts)}'; known = {}
            scopes = ((1, initial), (2, snapshot['parents']),
                      (4, snapshot['pooledPersonalHistories']), (8, snapshot['allPaidArchiveGenomes']))
            for mask, points in scopes:
                for point in points:
                    identity = key(point); birth = point['earliestKnownPaidFE']
                    assert birth <= snapshot['preBatchFE']
                    if identity not in known:
                        known[identity] = {'point': {k: point[k] for k in ('JS', 'FA', 'MA', 'WA', 'objectives')},
                                           'membership': 0, 'firstPaidFE': birth, 'firstRole': None}
                    record = known[identity]; record['membership'] |= mask
                    assert record['firstPaidFE'] == birth
                    origin = point.get('firstOriginRole', 'INITIALIZATION' if mask == 1 else None)
                    if origin is not None:
                        assert record['firstRole'] in (None, origin)
                        record['firstRole'] = origin
            entries = sorted(known.values(), key=lambda row: (row['firstPaidFE'], key(row['point'])))
            ids = {}
            for index, entry in enumerate(entries):
                entry['id'] = f'g{index}'; ids[key(entry['point'])] = entry['id']
                if entry['firstRole'] is None:
                    assert entry['membership'] == 2
                    entry['firstRole'] = 'UNKNOWN_CURRENT_ONLY'
                fields = [context_id, entry['id'], str(entry['membership']), str(entry['firstPaidFE']), entry['firstRole']]
                fields += [','.join(map(str, entry['point'][k])) for k in ('JS', 'FA', 'MA', 'WA', 'objectives')]
                guide_lines.append('\t'.join(fields))
            center = [p for p in snapshot['parents'] if p['role'] == 'CENTER']; assert len(center) == 55
            free = [(index, p) for index, p in enumerate(center) if p['category'] == 0]; assert len(free) == 47
            recipients = []
            for index in range(8):
                owner, parent = free[index * 46 // 7]
                history = [p for p in snapshot['pooledPersonalHistories'] if p['ownerRole'] == 'CENTER'
                           and p['ownerIndex'] == owner]
                assert history
                record = {'recipient': index, 'ownerIndex': owner,
                          'parentId': ids[key(parent)], 'personalId': ids[key(history[0])]}
                recipients.append(record)
                recipient_lines.append('\t'.join([context_id, str(index), record['parentId'], record['personalId']]))
            contexts.append({'id': context_id, 'sourceSeed': seed, 'step': snapshot['step'],
                'preBatchFE': snapshot['preBatchFE'], 'background': snapshot['preBatchArchive'],
                'entries': entries, 'recipients': recipients})
    assert len(contexts) == 6
    write_once(root / stem / 'contexts.json', contexts)
    (root / stem / 'guides.tsv').write_text('\n'.join(guide_lines) + '\n', encoding='utf-8')
    (root / stem / 'recipients.tsv').write_text('\n'.join(recipient_lines) + '\n', encoding='utf-8')
    return len(guide_lines) + 3840
