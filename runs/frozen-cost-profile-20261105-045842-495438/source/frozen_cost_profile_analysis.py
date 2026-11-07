"""Summarize sampled stacks, restricted to the actual RunContext.run search call tree."""
from collections import Counter
from run_long_budget_bridge import read, write_once


def stack_methods(event):
    frames = (event['values'].get('stackTrace') or {}).get('frames') or []
    return [f"{f['method']['type']['name'].replace('/', '.')}.{f['method']['name']}" for f in frames]


def summarize(path):
    events = read(path)['recording']['events']
    leaves, inclusive, allocations = Counter(), Counter(), Counter()
    cpu_all, cpu_search, allocation_events, truncated = 0, 0, 0, 0
    for event in events:
        values = event['values']; methods = stack_methods(event)
        thread = values.get('sampledThread', values.get('eventThread', {})) or {}
        if thread.get('javaName', thread.get('osName')) != 'main':
            continue
        is_search = 'org.uma.jmetal.util.research.runtime.RunContext.run' in methods
        if event['type'] == 'jdk.ExecutionSample':
            cpu_all += 1
            if not is_search:
                continue
            cpu_search += 1
            truncated += bool((values.get('stackTrace') or {}).get('truncated'))
            if methods:
                leaves[methods[0]] += 1
            inclusive.update(set(methods))
        elif event['type'] == 'jdk.ObjectAllocationSample' and is_search:
            allocation_events += 1
            name = (values.get('objectClass') or {}).get('name', 'unknown').replace('/', '.')
            allocations[name] += int(values.get('weight', 0))
    top = lambda counts: [{'name': name, 'samples': n, 'pctOfSearchCpuSamples': 100*n/cpu_search if cpu_search else None}
                          for name, n in counts.most_common(25)]
    return {'mainThreadCpuSamples': cpu_all, 'searchCpuSamples': cpu_search, 'truncatedSearchStacks': truncated,
        'topLeafMethods': top(leaves), 'topInclusiveMethods': top(inclusive),
        'searchAllocationSamples': allocation_events,
        'sampledAllocationWeightBytes': sum(allocations.values()),
        'topSampledAllocationWeights': [{'class': name, 'weightBytes': n} for name, n in allocations.most_common(20)],
        'scope': 'Sampled evidence, not exact method timers or total allocated bytes. CPU percentages conditioned on '
                 'main-thread samples containing RunContext.run; inclusive percentages overlap. Startup and return QA excluded by stack, '
                 'except inlining/truncation can make some samples unclassifiable. Not an algorithm performance comparison.'}


def analyze(root, cases):
    output = []
    for case in cases:
        path = root/case['stem']/case['method']
        result = summarize(path/'jfr-events.json')
        write_once(path/'profile-summary.json', result)
        output.append({**case, **result})
    result = {'cases': output, 'searchFE': 500000*len(output),
              'scope': 'Only cost discovery on frozen development traces; no new algorithm, quality gate or same-time claim.'}
    write_once(root/'analysis.json', result)
    return result
