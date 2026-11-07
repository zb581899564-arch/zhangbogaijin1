"""Pure encoded compatibility: local job-set keys and deterministic disjoint-cover witnesses."""
from itertools import product


def blocks(point, factories):
    js = point['JS']; n = len(js)
    assert sorted(js) == list(range(n)) and all(len(point[k]) == n for k in ('FA', 'MA', 'WA'))
    assignment = [None] * n; result = []
    for job, factory in zip(js, point['FA']):
        assert 0 <= factory < factories
        assignment[job] = factory
    for factory in range(factories):
        positions = [i for i, f in enumerate(point['FA']) if f == factory]
        assert positions, 'Source contains an empty factory'
        jobs = tuple(js[i] for i in positions)
        code = (jobs, tuple(point['MA'][i] for i in positions), tuple(point['WA'][i] for i in positions))
        mask = sum(1 << j for j in jobs)
        result.append((mask, code))
    return tuple(assignment), tuple(result)


def novel_covers(by_factory, observed, jobs, node_limit=250000, witness_limit=256):
    """Bounded exact feasibility search, not a proof of complete absence after hitting a limit."""
    choices = [sorted(options) for options in by_factory]
    order = sorted(range(len(choices)), key=lambda f: (len(choices[f]), f))
    suffix_union = [0] * (len(order) + 1)
    for i in range(len(order) - 1, -1, -1):
        value = 0
        for mask in choices[order[i]]: value |= mask
        suffix_union[i] = value | suffix_union[i + 1]
    full = (1 << jobs) - 1; selected = [None] * len(order); witnesses = []; nodes = 0

    def visit(position, covered):
        nonlocal nodes
        if nodes >= node_limit or len(witnesses) >= witness_limit: return
        if (covered | suffix_union[position]) != full: return
        factory = order[position]
        candidates = [full ^ covered] if position == len(order) - 1 else choices[factory]
        for mask in candidates:
            if nodes >= node_limit or len(witnesses) >= witness_limit: return
            nodes += 1
            if mask not in by_factory[factory] or mask & covered: continue
            selected[factory] = mask
            if position == len(order) - 1:
                key = tuple(selected)
                if key not in observed: witnesses.append(key)
            else: visit(position + 1, covered | mask)
    visit(0, 0)
    return {'novelCoverWitnesses': witnesses, 'nodesExamined': nodes,
            'nodeLimitReached': nodes >= node_limit, 'witnessLimitReached': len(witnesses) >= witness_limit,
            'exhaustive': nodes < node_limit and len(witnesses) < witness_limit}


def analyze_points(entries, factories, jobs):
    groups = {}; local = [{} for _ in range(factories)]; observed = set()
    for source_index, entry in enumerate(entries):
        partition, pieces = blocks(entry['point'], factories)
        group = groups.setdefault(partition, [set() for _ in range(factories)])
        observed.add(tuple(mask for mask, code in pieces))
        for factory, (mask, code) in enumerate(pieces):
            group[factory].add(code)
            local[factory].setdefault(mask, {}).setdefault(code, []).append(source_index)
    enrichment = []
    for partition, own in groups.items():
        masks = [sum(1 << j for j, f in enumerate(partition) if f == factory) for factory in range(factories)]
        extras = []
        for factory, mask in enumerate(masks):
            extra = sorted(set(local[factory][mask]) - own[factory])
            if extra:
                code = extra[0]
                extras.append({'factory': factory, 'extraDistinctBlocks': len(extra),
                    'firstWitness': {'jobs': code[0], 'machines': code[1], 'workers': code[2],
                                     'sourceIndex': min(local[factory][mask][code])}})
        enrichment.append({'assignmentByJob': partition, 'extraFactories': extras})
    cover = novel_covers([set(pool) for pool in local], observed, jobs)
    for witness in cover['novelCoverWitnesses']:
        assert sum(mask.bit_count() for mask in witness) == jobs
        assert sum(witness) == (1 << jobs) - 1
    enriched = sum(bool(p['extraFactories']) for p in enrichment)
    return {'sourceGenomes': len(entries), 'observedAssignments': len(groups),
        'localDistinctJobSetsByFactory': [len(p) for p in local],
        'localDistinctEncodedBlocksByFactory': [sum(len(v) for v in p.values()) for p in local],
        'enrichedAssignments': enriched, 'enrichedAssignmentFraction': enriched / len(groups),
        'assignmentEnrichment': enrichment, **cover}


def fixtures():
    observed = {(3, 12, 48, 192), (5, 10, 48, 192), (3, 12, 80, 160)}
    pools = [{p[f] for p in observed} for f in range(4)]
    expected = {p for p in product(*(sorted(v) for v in pools))
                if sum(v.bit_count() for v in p) == 8 and sum(p) == 255 and p not in observed}
    actual = novel_covers(pools, observed, 8)
    assert actual['exhaustive'] and set(actual['novelCoverWitnesses']) == expected == {(5, 10, 80, 160)}
    # The same canonical assignment is independent of global interleaving, but local order is retained.
    a = {'JS': [0, 1, 2, 3], 'FA': [0, 1, 0, 1], 'MA': [0] * 4, 'WA': [0] * 4}
    b = {'JS': [1, 0, 3, 2], 'FA': [1, 0, 1, 0], 'MA': [0] * 4, 'WA': [0] * 4}
    assert blocks(a, 2) == blocks(b, 2)
    limited = novel_covers(pools, observed, 8, node_limit=1)
    assert limited['nodeLimitReached'] and not limited['exhaustive']
    return {'status': 'PASS', 'cartesianCoverFixture': True, 'canonicalFactoryEncodingFixture': True,
            'boundedSearchNotClaimedExhaustive': True, 'searchFE': 0, 'decoderCalls': 0}
