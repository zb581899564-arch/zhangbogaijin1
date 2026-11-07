"""Known-state unscored compatibility audit, not a search or a modified optimizer."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, rows, read, write_once, execute, controller_lock
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from joint_family_oracle import analyze

SOURCE = ROOT/'runs/qpa-capability-pilot-20261106-025546-344483'


def build(root):
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    for path in (ROOT/'src/algorithms/diagnostics/joint_family').glob('*.java'):
        shutil.copy2(path, source)
    for name in ('run_joint_family_contract_audit.py', 'joint_family_oracle.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (SOURCE/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root/'compile.log')
    cp = str(classes)+';'+base; (root/'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root/'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json', class_hashes(classes)); return cp


def one(root, cp, stem, seed):
    out = root/stem/str(seed); out.mkdir(parents=True); points = rows(SOURCE/stem/str(seed)/'FE500K-FULL_SHARED_DEEP/initial-population.jsonl')
    assert len(points) == 100
    path = out/'known-initials.tsv'
    with path.open('x', encoding='utf-8') as stream:
        for point in points:
            fields = [','.join(repr(v) for v in point['objectives'])]
            fields += [','.join(map(str, point[k])) for k in ('JS', 'FA', 'MA', 'WA')]
            stream.write('\t'.join(fields)+'\n')
    inputs = root/stem/'inputs'
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.JointFamilyAuditRun',
           str(inputs/(stem+'.txt')), str(inputs/'RECONSTRUCTED-setup.txt'), str(path), str(out/'audit')]
    write_once(out/'command.json', cmd); print('JOINT_FAMILY_STRUCTURAL_AUDIT', stem, seed, flush=True)
    execute(cmd, out/'run.log', timeout=300)
    receipt, = rows(out/'audit/receipt.jsonl'); capture, = rows(out/'audit/loaded-identity.jsonl')
    write_once(out/'identity-verified.json', verify_capture(capture, cp))
    result = analyze(points, receipt); write_once(out/'independent-oracle.json', result)
    write_once(out/'source-identity.json', {'knownInitials': str(SOURCE/stem/str(seed)/'FE500K-FULL_SHARED_DEEP/initial-population.jsonl'),
        'sourceSHA256': digest(SOURCE/stem/str(seed)/'FE500K-FULL_SHARED_DEEP/initial-population.jsonl')})
    return {'stem': stem, 'seed': seed, **result}


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        assert read(SOURCE/'post-audit.json')['passed']
        root = ROOT/'runs'/datetime.now().strftime('joint-family-contract-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('JOINT_FAMILY_CONTRACT_ROOT', root, flush=True); before = protected()
        write_once(root/'protocol.json', {'version': 'JOINT_QGS_FAMILY_COMPATIBILITY-v1', 'registered': '2026-11-06',
            'source': str(SOURCE), 'instances': ['20_8_5_1', '100_2_3_1'], 'sourceSeeds': [14730003, 14730037],
            'fixtureScope': 'Eachfixed20parent xall100donors xallNsingletons+fullmask; eachfree80parent xall100donors xfullmask. NativePaMixingMove and actualFamilyContexts.restore; originalclassbytes, no policy override',
            'unscoredFixtures': 520000, 'newSearchFE': 0, 'decoderCalls': 0, 'objectiveUse': 'Onlyimportalready-paid initial objectives for frozen grouping checks; no objective computation, candidate ranking, learning or feedback',
            'guard': 'Problem.evaluate throws if called; sourceencodingsimmutable; independentbyjob integeroracle checks allaggregatecounts and witnesses',
            'interpretation': 'Structural compatibility evidence only, not performance loss caused by projection. Equalweight parent/donor coverage is not QGS actual guide distribution',
            'defaultMainlineChanged': False, 'goalAchieved': False})
        try:
            cp = build(root); results = []
            for stem in ('20_8_5_1', '100_2_3_1'):
                shutil.copytree(SOURCE/stem/'inputs', root/stem/'inputs')
                for seed in (14730003, 14730037):
                    results.append(one(root, cp, stem, seed))
            assert sum(r['fixtures'] for r in results) == 520000 and protected() == before
            assert class_hashes(root/'classes') == read(root/'class-hashes.json')
            for name, sha in read(root/'source-hashes.json').items():
                assert digest(root/'source'/name) == sha
            write_once(root/'analysis.json', {'contexts': results, 'fixtures': 520000, 'newSearchFE': 0, 'decoderCalls': 0,
                'nativeProgramDropInEquivalent': False, 'defaultMainlineChanged': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root/'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'newSearchFE': 0, 'decoderCalls': 0}); raise
        write_once(root/'status.json', {'status': 'COMPLETE', 'fixtures': 520000, 'newSearchFE': 0, 'decoderCalls': 0, 'goalAchieved': False})
        print('JOINT_FAMILY_CONTRACT_COMPLETE', results, flush=True)


if __name__ == '__main__':
    main()
