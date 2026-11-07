"""Audit author archive notifications at objective-box early exits; no optimizer or scheduling call."""
import csv
from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT, write_once, controller_lock
from run_gomea_native_semantics import MO, extract, run
from gomea_archive_harness import PREFIX, MAIN


def cases():
    a, b, c = [1.9, 2.1, 1.], [.5, 2.9, 1.], [1.8, 2.95, 1.]
    return [
        {'name': 'grid_same_box_before_dominator', 'grid': 1, 'archive': [a, b], 'parent': a,
         'candidate': c, 'expected': [0, 0, 2, 1], 'exactWholeArchiveDominated': True},
        {'name': 'grid_dominator_before_same_box', 'grid': 1, 'archive': [b, a], 'parent': a,
         'candidate': c, 'expected': [0, 1, 2, 0], 'exactWholeArchiveDominated': True},
        {'name': 'exact_order_a_b', 'grid': 0, 'archive': [a, b], 'parent': a,
         'candidate': c, 'expected': [0, 1, 2, 0], 'exactWholeArchiveDominated': True},
        {'name': 'exact_order_b_a', 'grid': 0, 'archive': [b, a], 'parent': a,
         'candidate': c, 'expected': [0, 1, 2, 0], 'exactWholeArchiveDominated': True},
        {'name': 'grid_equal', 'grid': 1, 'archive': [a, b], 'parent': a,
         'candidate': a, 'expected': [0, 0, 2, 1], 'exactWholeArchiveDominated': False},
        {'name': 'grid_new_pareto_point_same_box', 'grid': 1, 'archive': [a, b], 'parent': a,
         'candidate': [1.5, 2.5, 1.], 'expected': [0, 0, 2, 1], 'exactWholeArchiveDominated': False},
        {'name': 'exact_new_pareto_point', 'grid': 0, 'archive': [a, b], 'parent': a,
         'candidate': [1.5, 2.5, 1.], 'expected': [1, 0, 3, 1], 'exactWholeArchiveDominated': False},
        {'name': 'strictly_better_than_all', 'grid': 1, 'archive': [a, b], 'parent': a,
         'candidate': [0., 0., 0.], 'expected': [1, 0, 1, 1], 'exactWholeArchiveDominated': False},
        {'name': 'empty_archive', 'grid': 0, 'archive': [], 'parent': a,
         'candidate': c, 'expected': [1, 0, 1, 1], 'exactWholeArchiveDominated': False}]


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        root = ROOT / 'research/gomea_reference_audit' / datetime.now().strftime('native-semantics-archive-%Y%m%d-%H%M%S-%f')
        root.mkdir(); print('GOMEA_ARCHIVE_AUDIT_ROOT', root, flush=True)
        write_once(root / 'protocol.json', {
            'purpose': 'Original archive notification and normal CENTER predicate, finite state fixtures only',
            'originalSource': str(MO), 'originalFunctionBodiesUnchangedExceptLF': True,
            'storageHarness': 'Fixed capacity32 arrays; insertion and ordered removal; original objective-box, Hamming and Pareto functions',
            'objectiveDirections': 'Three MIN, all feasible, box width1; two mutually nondominated archive points in distinct boxes',
            'limits': 'Not full archive adaptation, optimizer, dynamic scheduling or measured performance effect',
            'fixtureCorrection': 'First retained0FE audit153653-307054 used candidate x1.95, itself dominated by first point; corrected to1.8 so first point trades off and second dominates. Original source unchanged.',
            'optimizationFE': 0, 'decoderCalls': 0})
        try:
            names = ('betterFitness', 'equalFitness', 'constraintParetoDominates', 'constraintWeaklyParetoDominates',
                     'paretoDominates', 'weaklyParetoDominates', 'sameObjectiveBox', 'hammingDistanceInParameterSpace',
                     'hammingDistanceToNearestNeighborInParameterSpace', 'updateElitistArchiveWithReplacementOfExistedMember')
            functions, anchors = extract(MO, names)
            declarations = '\n'.join(body[:body.index('{')].strip() + ';' for body in functions.values())
            (root / 'native-archive.c').write_text(PREFIX + declarations + '\n'.join(functions.values()) + MAIN, encoding='utf-8')
            fixtures = cases(); write_once(root / 'cases.json', fixtures); write_once(root / 'source-anchors.json', anchors)
            lines = []
            for index, case in enumerate(fixtures):
                for i, first in enumerate(case['archive']):
                    for second in case['archive'][i + 1:]:
                        assert not all(a <= b for a, b in zip(first, second))
                        assert not all(a <= b for a, b in zip(second, first))
                flat = [index, case['grid'], len(case['archive']),
                        *[v for point in case['archive'] for v in point], *case['parent'], *case['candidate']]
                lines.append(' '.join(map(str, flat)))
            (root / 'cases.txt').write_text('\n'.join(lines) + '\n', encoding='ascii')
            compiler = shutil.which('gcc'); assert compiler
            run(root, [compiler, '--version'], 'compiler-version.log')
            run(root, [compiler, '-O2', '-std=c11', '-mfpmath=sse', '-msse2', 'native-archive.c', '-o', 'native-archive.exe', '-lm'], 'compile.log')
            run(root, [str(root / 'native-archive.exe'), 'cases.txt'], 'results.csv')
            records = list(csv.reader((root / 'results.csv').open(encoding='ascii'))); assert len(records) == len(fixtures)
            for index, (case, record) in enumerate(zip(fixtures, records)):
                observed = list(map(int, record)); assert observed == [index, *case['expected']], (case['name'], observed)
                point = case['candidate']
                dominated = any(all(a <= b for a, b in zip(old, point)) and any(a < b for a, b in zip(old, point)) for old in case['archive'])
                assert dominated == case['exactWholeArchiveDominated']
            write_once(root / 'analysis.json', {'sourceStateFixturesPass': len(fixtures),
                'normalCenterAcceptanceCanDependOnArchiveOrderWhenGridEnabled': True,
                'sourceDominatedFlagIsNotAlwaysWholeArchivePredicate': True,
                'measuredDynamicPerformanceEffect': False, 'optimizationFE': 0, 'decoderCalls': 0, 'goalAchieved': False})
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'optimizationFE': 0, 'decoderCalls': 0})
            raise
        write_once(root / 'status.json', {'status': 'COMPLETE', 'cases': len(fixtures), 'optimizationFE': 0, 'decoderCalls': 0})
        print('GOMEA_ARCHIVE_AUDIT_COMPLETE', len(fixtures), flush=True)


if __name__ == '__main__':
    main()
