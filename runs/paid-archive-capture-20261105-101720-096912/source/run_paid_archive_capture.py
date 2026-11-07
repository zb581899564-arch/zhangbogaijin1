"""Observer-only actual genotype/history capture after the zero-FE supply prerequisite."""
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_mating_pool_probe import capture
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from research.composition_oracle.volume import UncoveredVolume

SOURCE = ROOT / 'runs/mating-pool-probe-20261105-062648-478040'
PREREQUISITE = ROOT / 'runs/paid-archive-supply-20261105-101417-844572'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)

EXTRA_METHODS = '''
    private static List<Map<String,Object>> paidArchiveGenomes() {
        List<Map<String,Object>> values = new ArrayList<>();
        for (Object point : actualArchive.snapshot()) values.add(paidGenome((PermutationSolution<?>) point));
        return values;
    }
    private static List<Map<String,Object>> personalHistories() {
        List<Map<String,Object>> values = new ArrayList<>();
        for (Direction role : Direction.values()) {
            int index = 0;
            for (Particle particle : working.get(role)) {
                for (PermutationSolution<Integer> point : particle.personalArchive()) {
                    Map<String,Object> value = paidGenome(point);
                    value.put("ownerRole", role.name()); value.put("ownerIndex", index); values.add(value);
                }
                index++;
            }
        }
        return values;
    }
    private static Map<String,Object> paidGenome(PermutationSolution<?> point) {
        Long birth = known.get(key(point));
        if (birth == null || birth > paid) throw new AssertionError("Unpaid archive/history genotype");
        Object family = point.getAttribute("cooperation.family");
        return row("earliestKnownPaidFE", birth, "firstOriginRole", firstRoles.get(key(point)),
            "category", family == null ? 0 : (Integer)family + 1,
            "JS", new ArrayList<>(point.getVariables()), "FA", new ArrayList<>(point.getVariablesid()),
            "MA", new ArrayList<>((List<?>)point.getAttribute("machine")),
            "WA", new ArrayList<>(point.getVariablesworker()), "objectives", point.getObjectives().clone());
    }
'''


def build(root):
    src, classes = root / 'source', root / 'classes'; src.mkdir(); classes.mkdir()
    (src / 'original').mkdir()
    original = SOURCE / 'source/MatingSourceAudit.java'
    shutil.copy2(original, src / 'original')
    body = original.read_text(encoding='utf-8')
    body = replace(body, '    private static int generation;private static long paid;',
        '    private static int generation;private static long paid;\n'
        '    private static String producingRole = "INITIALIZATION";\n'
        '    private static final Map<String,String> firstRoles = new HashMap<>();')
    body = replace(body, '        paid=fee;known.putIfAbsent(key(s),fee);mirror.add(s.getObjectives());actualArchive=archive;',
        '        paid=fee;known.putIfAbsent(key(s),fee);firstRoles.putIfAbsent(key(s),producingRole);\n'
        '        mirror.add(s.getObjectives());actualArchive=archive;')
    body = replace(body, '        working.put(role,new ArrayList<>(parents));',
        '        producingRole=role.name();\n        working.put(role,new ArrayList<>(parents));')
    body = replace(body, '            "preBatchArchive",mirror.snapshot(),"parents",encodeWorking()));',
        '            "preBatchArchive",mirror.snapshot(),"parents",encodeWorking(),\n'
        '            "allPaidArchiveGenomes",paidArchiveGenomes(),"pooledPersonalHistories",personalHistories()));')
    body = replace(body, '    private static String key(PermutationSolution<?> s) {',
        EXTRA_METHODS + '\n    private static String key(PermutationSolution<?> s) {')
    (src / 'MatingSourceAudit.java').write_text(body, encoding='utf-8')
    shutil.copy2(Path(__file__), src)
    base = (SOURCE / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             str(src / 'MatingSourceAudit.java')], root / 'compile.log')
    cp = f'{classes};{base}'; (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe',
             'org.uma.jmetal.util.research.search.MatingSourceAudit',
             'org.uma.jmetal.util.research.search.Particle',
             'org.uma.jmetal.util.research.search.CanonicalHmopso'], root / 'loaded-identity.json')
    return cp


def analyze(root, spec):
    stem = spec['stem']; normal = spec['normalization']
    lower, scale = np.asarray(normal['lower']), np.asarray(normal['scale'])
    cases = []
    for seed in SEEDS:
        folder = root / stem / str(seed) / 'capture'
        initial = rows(folder / 'mating-initial-points.jsonl')
        for snap in rows(folder / 'mating-source-pools.jsonl'):
            archive, histories = snap['allPaidArchiveGenomes'], snap['pooledPersonalHistories']
            assert sorted(tuple(p['objectives']) for p in archive) == sorted(map(tuple, snap['preBatchArchive']))
            assert all(p['earliestKnownPaidFE'] <= snap['preBatchFE'] for p in archive + histories)
            assert all(p['firstOriginRole'] in ('INITIALIZATION', 'MAKESPAN', 'CENTER') for p in archive)
            controls = initial + snap['parents'] + histories
            scale_points = lambda points: (np.asarray([p['objectives'] for p in points]) - lower) / scale
            background = scale_points(controls)
            archive_points = scale_points(archive)
            refs = {}
            for ref in (1.25, 1.5, 2.):
                known = UncoveredVolume(background, (ref,) * 3)
                actual = UncoveredVolume(archive_points, (ref,) * 3)
                assert actual.background_hv + 1e-11 >= known.background_hv
                gains = known.gains(archive_points)
                refs[str(ref)] = {'strongControlHV': known.background_hv, 'paidArchiveHV': actual.background_hv,
                    'bestExtraSingleGainPctOfPaidHV': 100 * float(max(gains, default=0.)) / actual.background_hv,
                    'materialExtraPoints': int(sum(gains >= .001 * actual.background_hv)),
                    'firstOriginRolesOfMaterial': sorted({archive[i]['firstOriginRole'] for i, g in enumerate(gains)
                                                          if g >= .001 * actual.background_hv})}
            cases.append({'seed': seed, 'step': snap['step'], 'paidFE': snap['preBatchFE'],
                'paidArchiveGenomes': len(archive), 'pooledPersonalHistoryRows': len(histories), 'references': refs})
    material = [c for c in cases if c['references']['1.5']['materialExtraPoints'] > 0]
    seed_counts = {str(seed): sum(c['seed'] == seed for c in material) for seed in SEEDS}
    gate = len(material) >= 2 and all(seed_counts[str(seed)] > 0 for seed in SEEDS)
    result = {'stem': stem, 'materialBeyondPooledHistorySnapshots': len(material), 'materialBySeed': seed_counts,
              'worthTeacherValueProbe': gate, 'cases': cases,
              'scope': 'Full paid genotype availability only, after complete accepted-personal-history control. '
                       'No teacher selected, offspring created or performance superiority claimed. '
                       'First-generation CENTER windows cannot establish four-role supply.'}
    write_once(root / f'{stem}-analysis.json', result)
    return result


def main():
    assert read(PREREQUISITE / 'status.json')['worthCapturingPaidArchiveGenomes']
    root = ROOT / 'runs' / datetime.now().strftime('paid-archive-capture-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('PAID_ARCHIVE_CAPTURE_ROOT', root, flush=True)
    completed, qa = [], 0
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            write_once(root / 'protocol.json', {'source': str(SOURCE), 'prerequisite': str(PREREQUISITE),
                'instances': STEMS, 'seeds': SEEDS, 'plannedSuccessfulFE': 20400,
                'scope': 'Observer-only same5100FE first-global sources, not a new search policy.',
                'capture': 'At original three CENTER windows encode actual full paid archive and every '
                           'current particle personal history, with paid birth and first producing-role identity. '
                           'Original full100current and100initial retained. No RNG, evaluations or search offers added.',
                'engineering': 'Reuse original capture equivalence checks: full paid SHA, all FE fronts, '
                               'initials, final genomes, admissions, empty local ledger and operation counters '
                               'identical to frozen OFF. Observation time separated, no same-time claim.',
                'gate': 'After adding all accepted personal histories to initial+current control, '
                        'each instance>=2of6snapshots has extra actual paid genotype single gain>=0.1%of '
                        'paid HV, covering both seeds. Same normalization/ref1.5,1.25/2sensitivity. '
                        'Pass only permits a separately frozen same-parent teacher-value probe; failure '
                        'stops this additional genotype-supply route, no window/threshold/history filtering.',
                'limits': 'Not four-role cooperation, useful offspring or complete algorithm gain. '
                          'No mainline/Q/role/shared change, new selector, download or transfer.'})
            cp = build(root)
            for stem in STEMS:
                shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')
                for seed in SEEDS:
                    qa += capture(root, cp, stem, seed); completed.append([stem, seed])
            specs = {s['stem']: s for s in read(SOURCE / 'protocol.json')['instances']}
            results = [analyze(root, specs[stem]) for stem in STEMS]
            worth = all(r['worthTeacherValueProbe'] for r in results)
            write_once(root / 'analysis.json', {'instances': results, 'worthTeacherValueProbe': worth})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'completed': completed, 'error': str(error)})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'successfulFE': 20400, 'failedFE': 0,
        'fullPaidTraceEquivalent': True, 'returnedFullDecoderQA': qa, 'worthTeacherValueProbe': worth})
    print('PAID_ARCHIVE_CAPTURE_COMPLETE', 'worthTeacherValueProbe', worth, flush=True)


if __name__ == '__main__': main()
