"""Read-only final aggregation of complete/reused/failed engineering evidence. No decoder or search."""
from pathlib import Path
import sys

from run_long_budget_bridge import ROOT, read, rows, write_once
from research.semantic_repair.evidence import digest
from pa_capability_support import initial_key
from run_qpa_complete_engineering import protected
from ctx_gom_engineering_cases import fees


def completed_folder(root, stem, label):
    path = root/stem/label
    return Path(read(path/'reuse.json')['source']) if (path/'reuse.json').exists() else path


def all_costs(root):
    plan = read(root/'protocol.json'); result = fees(root); provenance = []
    for item in plan['previousRetainedRuns']:
        folder = Path(item['path']); counts = fees(folder)
        recovery = folder/'recovered-serialization-failure.json'
        if recovery.exists():
            recovered = read(recovery)
            for key in ('successfulFE','attemptedFE','failedFE','paidFullTimelineQA'):
                counts[key] += recovered[key]
        assert counts['attemptedFE'] == item['actualAttemptedFE']
        for key in result:
            result[key] += counts[key]
        provenance.append(dict(path=str(folder), costs=counts, originalStatus=read(folder/'status.json')['status']))
    return result,provenance


def summarize(root):
    analysis = read(root/'analysis.json'); protocol = read(root/'protocol.json')
    plan = protocol['prospectiveContract']; assert analysis['engineeringPass']
    assert protected() == protocol['protectedBefore']
    original_ids = read(root/'original-source-identities.json')
    assert all(digest(Path(info['path'])) == info['sha256'] for info in original_ids.values())
    cases = []
    for stem in plan['instances']:
        old = completed_folder(root,stem,'OFF-OLD-SHARE_CTX_GOM'); initial = initial_key(old)
        assert len(initial) == 100
        for label in ('OFF-NEW-SHARE_CTX_GOM','OFF-OLD-NSGA_CTX_GOM','OFF-NEW-NSGA_CTX_GOM',
                      'SHARE_CTX_GOM','SYNC_CTX_GOM','UNIFORM_CTX_GOM','NSGA_CTX_GOM'):
            out = completed_folder(root,stem,label); assert initial_key(out) == initial
            if label.startswith('OFF-'):
                continue
            receipt, = rows(out/'receipt.jsonl'); catalog, = rows(out/'catalog.jsonl')
            replay = read(out/'independent-replay.json'); search = receipt['search']
            n,f = catalog['jobs'],catalog['factories']
            if label == 'NSGA_CTX_GOM':
                boundary,center = 2*15*(2*n-1),2*55*(2*n-1); composed = None
            else:
                boundary = 2*(11*(2*n-1)+4*(2*n-f)); center = 2*(47*(2*n-1)+8*(2*n-f))
                composed = search['global.evaluations']-search['alignedKernelProposals']
                assert (composed == 0) == (label == 'SYNC_CTX_GOM')
                for group in range(1,5):
                    assert search[f'qgs.g{group}.updates'] == 100
                    assert sum(search.get(f'qgs.g{group}.action{a}',0) for a in range(3)) == 100
            actual = {int(k):v for k,v in replay['physicalRoleLocalFE'].items()}
            assert actual == {1:boundary,2:center,3:boundary,4:boundary}
            cases.append(dict(instance=stem,variant=label,source=str(out),successfulFE=receipt['successful'],
                completePasses=replay['completePasses'], localFE=receipt['gom']['localEvaluations'],
                physicalRoleLocalFE=actual,exactPaidCopyRecoveries=receipt['gom']['recoveredPaidCopies'],
                composedCandidatesValidatedByUnchangedRuntimeGuard=composed))
    combined,failures = all_costs(root); covered = fees(root,include_reused=True)
    assert combined['attemptedFE'] == analysis['combinedEngineeringAttemptedFE'] <= plan['maximumActualAttemptedFE']
    assert combined['failedFE'] == 0 and combined['paidFullTimelineQA'] == combined['successfulFE']
    result = dict(status='ENGINEERING_ACCEPTED',run=str(root),contractSHA256=protocol['contractSHA256'],
        coveredProtocolCases=covered, combinedActualCostsIncludingRetainedFailures=combined,
        retainedFailures=failures, mainCases=cases, initial100EqualAcrossAllEightSources=True,
        originalFrozenSourcesAndDefaultProtectedFilesUnchanged=True, newSearchFE=0, newDecoderCalls=0,
        performanceEvidence=False,defaultMainlineChanged=False,goalAchieved=False,
        limitation='Serialization failure retains all5102 paid objective/hash notifications and recovered objective front; encoded front unavailable for that failed pre-fix run. Final valid runs have full encodings.',
        next='Light-observer exact trajectory acceptance, then a separately frozen sameFE/realtime protocol jointly using HV, IGD+ and bidirectional C; old sharing, sourced Li, old strong NSGA, same-GOM NSGA, roles and sharing ablations required')
    write_once(root/'final-acceptance.json',result)
    return result


if __name__ == '__main__':
    root = Path(sys.argv[1]); result = summarize(root)
    print('CTX_GOM_FINAL_ACCEPTANCE',result['combinedActualCostsIncludingRetainedFailures'])
