"""Outcome-independent definition of the conditional mature-receiver supply probe."""
import json


def freeze(anchor, root):
    old = json.loads((anchor / 'protocol.json').read_text())
    value = {
        'version': 'MATURE_RECEIVER_SAME_PATH_DONOR_SUPPLY-v1', 'date': '2026-11-06',
        'instances': old['instances'], 'seeds': old['seeds'], 'arms': ['R', 'G', 'S', 'UNION'],
        'capture': 'First actual PRE_GLOBAL boundary with successfulFE>=250000, same six prior FULL paths',
        'sourceCharge': 'Six500k observation replays=3000000new FE; compare fullpaidSHA and common checkpoints to existing Linux FULL',
        'future': 'Only P at PRE_GLOBAL and the following5000paid proposals/A0 enter probes; later source continuation never imported',
        'P': '100 mature receivers, actual decomposition roles/families; not LOCAL_ONLY parents or a new PA restart',
        'G': 'All successful non-compose proposals in selected global block, including rejected proposals',
        'S': 'All successful composed proposals, only applicable fixed-family requests; no free80 supply expected',
        'pool': 'Same-family liveR excludingself plus frozen eligibleexternal. Dedup physical ordered factory job/MA/WA chains within family; remove states equal to initialR; union G/S overlap once asGS; stable firstpaid order',
        'mode': 'R=original live; G=R+G; S=R+S; UNION=ordinary R+G+S. No new selector or source balancing',
        'interactions': 'Source inclusion2x2 isolates G/S addition and S marginal over G; not an unregistered full algorithm factorial',
        'fixed': 'Receiver/model trainingP, family/legal domain, role/order, full FOS, joint moves and original acceptance',
        'archive': 'Each arm starts with identical POST_GLOBAL all-paid ND A0 in originalGomScope archive; evolves independently after probe evaluations',
        'rng': 'probeSeed=sourceSeed XOR0x51d0a7e3. Reencode/model order common. Each proposal draws nextInt(bound) from privateRandom(probeSeed XOR(0x632be59bd9b4e019*(slot+1)+0x9e3779b97f4a7c15*(step+1))) signed64. New isolated sampling interface, not native continuation',
        'externalViews': 'IndependentRandom(probeSeed XOR0x9e3779b97f4a7c15*firstPaidFE), shared acrossallarms; no workRNG advances',
        'probeFE': {'20_8_5_1': 3820, '100_2_3_1': 19860}, 'scienceProbeFE': 284160,
        'end': 'One complete100receiver pass, not500k final algorithm ranking. All candidates/fallback/repeats paid',
        'engineering': 'OriginalGomLocalProgram vs R_NATIVE fullpassdigest/working/archive equal; deterministicRrepeat; G/S/UNION fulltimeline QA; cutoff1/2/last-1; injectedfailure2; fullimportphysical QA',
        'engineeringAttemptedFE': 189448, 'engineeringExpectedFailures': 2,
        'totalPlannedAttemptedFE': 3473608,
        'comparisons': [['UNION','R'], ['G','R'], ['S','R'], ['UNION','G'], ['UNION','S']],
        'reference': 'Per-instance ND union all four arms and three source-seed finalA0+probe fronts; offline only',
        'normalization': 'Inherited frozen scales; HV1.5 with1.25/2.0; IGD+/IGD averageEuclidean and exactweakC counts',
        'decision': 'Only a conditional mechanism signal: preexisting tier1HV1% orIGDplusSymmetric5%, repeat>=2/3, otherinstance no majorHV-1/IGD-5/Cgap-10pp; no metric vote. Small newdelta/activation insufficient is inconclusive, not global no-value',
        'activation': 'Report pools/readrates/acceptance/admission and fixedfamily/free separately; fewer than20externalreads percontext means inadequately exercised, no stop-by-no-effect claim',
        'cost': 'Sourceactual, logical prefix+pass, import QA, fulltimelineQA, generation/loading/search/statistics separate; no TIME advantage',
        'reuseLimits': 'OldGRAFT50k+50k was independent source+newPArestart/staticND100; PRE_FIRST changed receiver ancestor; completed-donorfeedback changed Rvisibility. None changed only same-path matureP G/S availability',
        'stops': 'All prior stoppedalgorithms remain stopped. No capacity/ratio/window/seed scan; full registered batch before quality summaries',
        'goals': 'No Goal or backgroundjob; no defaultmainlinechanges; no automatic6000000FE expansion',
    }
    path = root / 'protocol.json'
    if path.exists():
        assert json.loads(path.read_text()) == value
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    return value
