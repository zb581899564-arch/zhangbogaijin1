"""Independent fixed-sample integer reconstruction and full structural accounting."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from collections import Counter
from pathlib import Path
import shutil
import sys

from run_long_budget_bridge import ROOT, read, write_once
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from qpa_geometry_audit_inputs import check_models
from qpa_geometry_audit_proposals import check_proposals


def identities(root, protocol):
    plan = protocol['contract']
    assert read(root/'status.json')['status'] == 'COMPLETE'
    assert protected() == protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/QPA_NEUTRAL_GEOMETRY_V1.json') == protocol['contractSHA256']
    assert digest(Path(plan['sourcePilot'])/'independent-final-audit.json') == plan['sourcePilotAuditSHA256']
    for name, sha in read(root/'source-hashes.json').items():
        assert digest(root/'source'/name) == sha
    for path, sha in read(root/'source-identities.json').items():
        assert digest(Path(path)) == sha
    assert class_hashes(root/'classes') == read(root/'class-hashes.json')
    for stem in ('20_8_5_1', '100_2_3_1'):
        for name, sha in read(root/stem/'input-hashes.json').items():
            assert digest(root/stem/'inputs'/name) == sha
            assert digest(Path(plan['sourcePilot'])/stem/'inputs'/name) == sha
        receipt = read(root/stem/'receipt.json')
        verify_capture(receipt['identity'], (root/'classpath.txt').read_text().strip())
        assert receipt['status'] == 'PASS' and receipt['error'] is None
        for key in ('attemptedSearchFE', 'successfulSearchFE', 'failedSearchFE', 'objectiveBackendCalls', 'dynamicDecoderCalls'):
            assert receipt[key] == 0


def audit(root):
    protocol = read(root/'protocol.json')
    plan, execution = protocol['contract'], protocol['execution']
    audit_plan = dict(systematicEveryRows=137, blockEndsAlso=True, maximumVerificationConstructions=2200,
        fullRecordAndModelChecks=True, rebuildAllProposals=False,
        originalSearchConstructions=read(root/'analysis.json')['unscoredCompleteProposalConstructions'],
        maximumCombinedConstructions=plan['maximumUnscoredCompleteProposalConstructions'],
        maximumNewSearchFE=0, maximumNewDecoderCalls=0)
    write_once(root/'audit-protocol.json', audit_plan)
    identities(root, protocol)
    result = read(root/'analysis.json')
    expected = {p['population']: p for p in result['populations']}
    instances, checked, total, verification = [], [], 0, 0
    for stem in ('20_8_5_1', '100_2_3_1'):
        data, models, catalog, statistics = check_models(root, stem, plan, execution)
        work, counts = check_proposals(root, stem, data, models, catalog, plan, execution, audit_plan)
        receipt = read(root/stem/'receipt.json')
        assert work['rows'] == receipt['unscoredCompleteProposalConstructions']
        assert receipt['modelBuilds'] == len(models)*2 == 88
        assert receipt['knownPhysicalCarrierInitializations'] == len(data)*100 == 4400
        for population in dict.fromkeys(key[0] for key in data):
            old = expected[population]
            overall = Counter()
            for view in old['views']:
                row, = [s for s in statistics if s['population'] == population and s['variant'] == view['variant']]
                assert row['nonSingletonFOSJaccard'] == view['nonSingletonFOSJaccard']
                assert abs(row['maximumQpaAffinityChange']-view['maxQpaAffinityChange']) < 1e-12
                if view['variant'] != 'ORIGINAL':
                    group = counts[population, view['variant']]
                    assert all(view[k] == value for k, value in group.items())
                    overall.update(group)
            assert dict(overall) == old['total']
            fraction = overall['qpaPhysicalChanged']/overall['qpaProposals']
            low = sum(v['nonSingletonFOSJaccard'] <= .8 for v in old['views'] if v['variant'] != 'ORIGINAL')
            assert fraction == old['aggregatePhysicalProposalChangedFraction'] and low == old['lowFOSJaccardViews']
            assert (low >= 8 and fraction >= .2) == old['coveragePass']
            checked.append(dict(population=population, evolved=old['evolved'], fraction=fraction, lowFOSJaccardViews=low))
        instances.append(dict(instance=stem, **work, modelsVerified=len(models), sourceModelBuilds=receipt['modelBuilds']))
        total += work['rows']
        verification += work['verificationConstructions']
    assert total == result['unscoredCompleteProposalConstructions']
    assert verification <= audit_plan['maximumVerificationConstructions']
    assert total + verification <= plan['maximumUnscoredCompleteProposalConstructions']
    evolved = [r for r in checked if r['evolved']]
    assert len(evolved) == 2 and result['necessaryCoveragePass'] == all(r['lowFOSJaccardViews'] >= 8 and r['fraction'] >= .2 for r in evolved)
    record = dict(passed=True, instances=instances, populations=checked, sourceProposalConstructions=total,
        independentVerificationConstructions=verification, combinedUnscoredConstructions=total+verification,
        allModelsAndCaseRowsChecked=True, paPhysicalGenesModelFOSAndProposalInvariant=True,
        proposalsIndependentlyRebuiltOnlyAtFixedSample=True, newSearchFE=0, newDecoderCalls=0,
        completeObjectiveQueries=0, performanceProved=False, goalAchieved=False)
    write_once(root/'independent-final-audit.json', record)
    destination = root/'independent-audit-source'
    destination.mkdir()
    for name in ('audit_qpa_neutral_geometry.py', 'qpa_geometry_audit_inputs.py', 'qpa_geometry_audit_proposals.py'):
        shutil.copy2(Path(__file__).with_name(name), destination)
    print('QPA_NEUTRAL_GEOMETRY_INDEPENDENT_AUDIT_PASS', total, verification, flush=True)


if __name__ == '__main__':
    audit(Path(sys.argv[1]).resolve())
