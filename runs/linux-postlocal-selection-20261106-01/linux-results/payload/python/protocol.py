"""Outcome-independent conditional post-local selection protocol."""
from prepare import write


def freeze(root):
    value = {
        'version': 'MATURE_PARENT_CHILD_POSTLOCAL_SELECTION-v1', 'date': '2026-11-06',
        'instances': ['20_8_5_1', '100_2_3_1'], 'seeds': [16110003, 16110037, 16110069],
        'arms': ['RAW_ROLE', 'POST_ROLE', 'POST_PARETO'],
        'source': 'Existing linux-mature-donor-20261106-01 capture: originalP100 and each role first raw child batch; all duplicates retained',
        'background': 'Same already paid POST_GLOBAL all-paid ND A0; conditional source cost, no future source state',
        'sourceNewFE': 0, 'sourceHistoricalFE': 3000000,
        'sourceLimitation': 'C100 combines role first batches at different FE, not synchronous reproduction or native full-QGS continuation',
        'raw': 'Original FULL_ROLE role/family parent-child selection before local; then three full native100member GOM passes',
        'post': 'P100 and C100 each polished one full native GOM pass; each private acceptance archive starts atA0; public archive includes allpaid; then role/family select100 and one full continuationpass',
        'paretoControl': 'Same POST polish, but FULL_ALL rank/crowding within physical role and fixed family quotas; local fourrole preferences unchanged',
        'privateArchive': 'RAW eachpass and POST finalpass start from current public A0+allpaid ND union; P/C polish independentA0 to isolate comparison',
        'localSemantics': 'Native GomLocalProgram, live donors, same model-learning rule per actual cohort. Models need not be numerically identical acrosscohorts',
        'rng': 'probeSeed=sourceSeed XOR0x6c8e9cf5L; RAW pass1=probeSeed/pass2=probeSeed XOR0x9e3779b97f4a7c15L signed64; POST P/C eachreset(probeSeed); allfinalpasses reset(probeSeed XOR0x51d0a7e3L) before nativeviews/models',
        'budget': 'Same3B actual evaluations perarm; RAW saved probe allocation spent on existing local search; allocation effects included',
        'passFE': {'20_8_5_1': 3820, '100_2_3_1': 19860}, 'scienceFE': 639360,
        'engineering': 'Eachcase firstseed RAWnative/RAWadapter/POST_ROLE/POST_PARETO full3B; POST_ROLE cutoffs1,2,B,2B,3B-1; expectedfailure2',
        'engineeringAttemptedFE': 426248, 'engineeringExpectedFailures': 2, 'totalPlannedAttemptedFE': 1065608,
        'physics': 'Every successful engineeringcandidate fulltimelineQA; imports200eachcontext checked once; no QA feedback',
        'comparisons': [['POST_ROLE', 'RAW_ROLE'], ['POST_ROLE', 'POST_PARETO'], ['POST_PARETO', 'RAW_ROLE']],
        'reference': 'Perinstance ND union all3arms x3seed finalallpaid fronts, offlineonly; oldfrozen scales HV1.5,1.25,2; IGD+/IGD/C',
        'endpoints': 'Final A0+allpaid archive primary; workingpopulation, 2B archives/selected working states, raw/post selection overlap explanatory',
        'gate': 'Tier1 material medianHV>=1% orIGDplus symmetric>=5%, sameinstance>=2/3repeat; otherinstance no majorHV<-1%, IGDplus<-5%, Cgap<-10pp; explain anyC reversal; no score/vote',
        'ordinaryControl': 'POST_PARETO matching means no extra role-selection-specific claim; no automatic promotion of control',
        'noTautology': 'All tested unselected candidates remain in allpaid; retained quality alone cannot pass. Continuation and equal3B final outcome required',
        'oldFailures': 'Not PRE_FIRST choosingoldroot, not R/G/S donor availability, not phasepreference or finalG+L retention, not missing elitism repair',
        'limits': 'Alreadyused development states; no full500k/nativecontinuation, TIME_LIMIT, independentvalidation, or noveltyclaim',
        'preserved': 'Originalfourroles QGS fixedFA families sharing generator and production default source; no newdonorratio/cap/selector learning',
        'stopping': 'No seed/window/ratio/length scans; completebatch before qualitysummary; failures retained; no Goal/background or automaticexpansion',
    }
    write(root / 'protocol.json', value)
    return value
