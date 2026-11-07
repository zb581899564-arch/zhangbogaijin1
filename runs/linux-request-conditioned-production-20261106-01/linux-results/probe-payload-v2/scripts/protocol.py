"""Outcome-independent, fixed-model conditional production probe."""
from common import write

ARMS = ['ROLE', 'REQUEST', 'ORDINARY', 'SHUFFLED']


def freeze(root):
    plan = dict(version='REAL_REQUEST_CONSTRAINED_PRODUCTION-v1', arms=ARMS,
        question='Can real receiver cap change useful donor production beyond original role preferences and generic constrained search?',
        dependency='source-protocol.json; all source-equivalence gates must pass first',
        sampling='Two existing instances, three existing source seeds, seedIndex%4 family, its first four actual requests in the frozen mature global phase; unavailable requests are missing, not resampled',
        budgetPerArm=512, productionFE=511, compositionFE=1, maximumScienceFE=49152,
        sourceAdditionalFE=1618320,
        commonState='Mature pre-global 100P and family-conditioned GOM model; only selected family five slots execute; request-specific retained pool; common post-global already-paid archive A0',
        stateLimit='Conditional delayed batch experiment. Each older request is replayed from one common post-global information barrier, so shuffled requests contain no future information relative to the experiment. Not immediate online feedback',
        representation='Unchanged fixed-FA job sets, original PaMixingMove and FOS construction, live accepted family donors',
        schedule='Five slots round robin over their shuffled original FOS, reshuffle when exhausted; 103/102/102/102/102 production evaluations, CENTER has two slots. Same schedule all arms; not a complete native GOM pass',
        constraints='Only the genuine request cap is a production feasibility constraint; sum_f max(C_f-cap,0)/cap. No invented TEC/TWC upper bounds',
        acceptance={
            'ROLE': 'Original role-specific GOM acceptance, no cap constraint',
            'REQUEST': 'Lower cap violation wins, greater loses, equal violation uses original role-specific GOM acceptance',
            'ORDINARY': 'Same cap feasibility first; equal violation uses strict decrease of TEC/energyScale + eta*TWC/wageScale for every slot',
            'SHUFFLED': 'Same as REQUEST but uses next sampled request cap, cyclic shift1 within same source and fixed FA family'},
        center='Original CENTER weak Pareto improvement or absence of strict domination in private paid archive; no new center preference',
        eta='Used by ordinary constrained control and original final sharing selector. REQUEST and SHUFFLED do not use eta in production acceptance',
        selection='Every arm uses the actual target cap/eta and unchanged FactoryPool rules; all successful production candidates offered. Last FE evaluates original composed selection, or target parent fallback when impossible/duplicate',
        pool='Preserve original retained ordering, exact nondominance, max8 truncation and weighted feasible selector; any isolated adapter must be checked against original classes',
        accounting='All 511 attempted production candidates including duplicates/rejections and final assembly charged; all successful candidates enter common reporting archive. Failures consume FE and are retained',
        imports='Re-decode already paid source genomes and retained factory encodings to validate/restore metadata; count these separately. No reconstructed QA-only whole schedule enters search or reporting archive',
        rng='sourceSeed XOR 0x37a9185bL XOR requestIndex*0x9e3779b9L; equal starts across arms, paths may diverge. No assertion of identical later candidates',
        observations='No online HV or IGD; observe acceptance, constraint overrides, unique pool supply, final selection and all paid archive. Observation cost separate where measured; no same-time claim',
        reference='Per instance ND union of all four arms, all selected requests and seeds final reporting fronts; fixed original normalization; HV1.5 with1.25/2, mean nearest IGD+/IGD, exact weak bidirectional C with counts',
        aggregation='Requests within a seed are paired diagnostic subcases, not independent seeds. Aggregate request-paired effects within each seed, then show three source seeds and their median/range/signs',
        primary='Final A0+all-paid archive, REQUEST vs ROLE and vs ORDINARY and vs SHUFFLED together; pool feasibility, request scoring and final composition are explanatory',
        gate='Material signal: paired median HV>=1% or IGD+ symmetric improvement>=5%, repeated in at least2/3 source seeds of one instance; other instance no median HV<-1%, IGD+<-5%, or Cgap<-10pp. Explain contrary C/region evidence, no weighted vote',
        specificClaim='A role-request-specific claim requires advantage over ordinary constraint and shuffled matching; if ordinary explains gain, do not claim four-group specificity',
        inactive='If constraints or shuffle rarely change choices, report insufficient exposure; do not reject broad hypothesis or resample to force activation',
        stopping='Complete registered batch before quality review. No extra seeds, request windows, caps, budget lengths, ratios, instances or automatic control promotion',
        forbidden='No default mainline change, full algorithm integration, full500k competitive experiment, TIME_LIMIT, classical matrix, Goal or daemon',
        engineering='Original pool equivalence; imported objective and fixed-FA checks; complete dynamic timeline on engineering paid candidates; repeat and observer on/off; cutoff1/2/511/512 and injectedfailure2; independent acceptance/all-paid archive/metric review')
    write(root / 'protocol.json', plan)
    return plan

