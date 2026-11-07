"""Frozen two-stage pilot for one exit decision, with matched strong classical controls."""
from run_long_budget_bridge import ROOT, read

AUDIT = ROOT / 'runs/program-acceptance-audit-20261105-133301-840955'
BASELINE = ROOT / 'runs/local-program-audit-20261105-123427-539293'
SOURCE = ROOT / 'runs/natural-regime-bench-20261105-073626-086353'
SEEDS = (13390003, 13390037)
ARMS = ('FULL_OFF', 'FULL_ON', 'NSGA_OFF', 'NSGA_ON')
FE_LIMIT, TIME_FE_CAP = 100000, 500000


def order(budget):
    result = []
    for instance_index, spec in enumerate(read(SOURCE / 'protocol.json')['instances']):
        for seed_index, seed in enumerate(SEEDS):
            offset = (instance_index + seed_index + (budget == 'TIME')) % len(ARMS)
            result += [{'stem': spec['stem'], 'seed': seed, 'arm': arm, 'budget': budget}
                       for arm in ARMS[offset:] + ARMS[:offset]]
    return result


def protocol():
    return {'instances': read(SOURCE / 'protocol.json')['instances'], 'opportunityAudit': str(AUDIT),
        'engineeringBaseline': str(BASELINE), 'seeds': SEEDS, 'arms': ARMS,
        'orderFE': order('FE'), 'orderTIME': order('TIME'),
        'hypothesis': 'CENTER whole-program exit selection using fixed-reference geometric improvement '
                      'can turn independently witnessed PDDR rejections into useful continuation, preserving '
                      'boundary responsibilities and common inner search. Four-group benefit must survive '
                      'equally enhanced NSGA, not merely beat its old acceptance.',
        'intervention': 'Only original LocalSearch.vns outer comparison of improved vs incumbent changes '
                        'for CENTER: accept iff HV(R+improved)>HV(R+incumbent)+1e-10, R identical frozen '
                        'global-post100reference, original normalization, referencePoint1.5. Inner descent '
                        'and inter-factory acceptance remain original PDDR. Boundary preferences, QGS, '
                        'pbest/Q updates, families, sharing, generation survival and all neighborhoods unchanged.',
        'implementation': 'Exact3D numeric sweep; nondominated reference pruning and per-reference objective '
                          'score memoization affect only indicator cost, never skip a scheduling evaluation. '
                          'No decoder in metric. Cache reference immutability verified in runtime audit. '
                          'All construction/selection/indicator/archive costs included in real search time.',
        'engineering': 'Resolve frozen source and actual runtime classes/JDK/SHA. Python independentHV '
                       'fixtures include systematically sampled old real comparisons and numeric boundary cases. '
                       'Four100kOFF runs must equal old full paidSHA, initials, fronts/genes/birthFE, ledger, '
                       'search and decoder counts. Four100kON audit runs must independently reproduce every '
                       'actual CENTER outer HV score and decision, and original PDDR counterfactual. '
                       'Twoinstances ONcutoffs1/2/5100/10000, strictfees/fullQA. All before new-seed performance.',
        'budget': 'Engineering830206successfulFE=4*100kOFF+4*100kON+2*(1+2+5100+10000). '
                  'StageA16runs*100k=1600000successfulFE. Only if ALL StageA gates pass, StageB16true '
                  'TIME_LIMIT runs4/5seconds, each500kFE safety cap. Hitting cap invalidates TIME result. '
                  'Single sequential JVM Xms32m/Xmx2g, no external transfer. Preserve all failures and costs.',
        'pairing': 'Same instance/model/SUT/parameters and initial100genomes/objectives for all4arms perseed. '
                   'OFF/ON withinmethod must match first5100 globalFE. FE/TIME samearm common reached '
                   'FE checkpoints equal. Changed decisions advance RNG differently; do not claim matching '
                   'later candidates or natural per-slot expenditures. No audit trace in timed science.',
        'metrics': 'PrimaryHV1.5 at100kFE and trueT; fixed original scales, sensitivity1.25/2.0. '
                   'IGD+ against empiricalND union of4arms*2seeds perinstance/budget; no search use. '
                   'Every seed and all reached curves reported. Conditional audit gain sum is not predicted '
                   'algorithm gain and does not enter performance metrics.',
        'gate': 'Retain preceding pilot standards: EACHinstance FE medianFULL_ON/FULL_OFF>=0%, '
                'everypair>=-0.5%; medianvsNSGA_ON>=-1%, everypair>=-5%. '
                'Reference1.25/2 medians>=0vsown and>=-2%vsmatchedNSGA; IGD+symmetrical worsening '
                'median<=5%vsmatchedNSGA. Bothinstances necessary to START StageB. '
                'StageB same conditions plus medianFULL_ON/FULL_OFF>=0.5%. '
                'Pass only permits separate500k/fullrole/sharing/Li/commonbaseline comparisons and '
                'newinstances+independentconfirmation, never goal completion or paper advantage.',
        'stop': 'Failing StageA skipsTIME and stops this exactCENTER exit-HV rule. No reference/scales/threshold '
                'scan, moving HV to inner/inter/pbest, source subset, seed or time retuning to rescue it. '
                'No retrospective control promotion. Prior identity-shake, reference replacement, scalar '
                'tasks, parent reweighting, prefix copying and conditional-exchange stops unchanged.',
        'novelty': 'Indicator-based selection and local search are established; this is targeted mechanism '
                   'verification, not a claim that usingHV is novel. Same operator in both algorithms '
                   'required. Four roles and existing conditional sharing remain protected default mainline.'}
