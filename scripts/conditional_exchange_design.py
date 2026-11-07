"""Parameter-free conditional exchange, distinct from the stopped whole-empty-neighborhood precheck."""
from run_long_budget_bridge import ROOT, read

AUDIT = ROOT / 'runs/candidate-redundancy-20261105-120604-024210'
BASELINE = ROOT / 'runs/factory-cache-potential-20261105-082934-494793'
SOURCE = ROOT / 'runs/natural-regime-bench-20261105-073626-086353'
SEEDS = (13190007, 13190037)
ARMS = ('FULL_OFF', 'FULL_ON', 'NSGA_OFF', 'NSGA_ON')
FE_LIMIT, TIME_FE_CAP = 100000, 500000


def order():
    result = []
    for budget_index, budget in enumerate(('FE', 'TIME')):
        for instance_index, spec in enumerate(read(SOURCE / 'protocol.json')['instances']):
            for seed_index, seed in enumerate(SEEDS):
                offset = (budget_index + instance_index + seed_index) % len(ARMS)
                result += [{'stem': spec['stem'], 'seed': seed, 'arm': arm, 'budget': budget}
                           for arm in ARMS[offset:] + ARMS[:offset]]
    return result


def protocol():
    return {'instances': read(SOURCE / 'protocol.json')['instances'], 'sourceAudit': str(AUDIT),
        'seeds': SEEDS, 'arms': ARMS, 'order': order(),
        'hypothesis': 'Removing incidental equal-valued resource exchanges by exact conditional '
                      'sampling, with nonempty support, improves useful progress per paid evaluation '
                      'enough to improve the four-duty method and compete with equally enhanced NSGA.',
        'distinctFromStoppedHypothesis': 'The four-cell >=5%whole-empty gate failed and stays stopped. '
                 'Do NOT skip an empty neighborhood. When all values equal, call original generator '
                 'and pay original identity evaluation. No historical duplicate filtering, caching '
                 'or withoutreplacement memory. The new object is random pair selection inside '
                 'nonempty resource-exchange operators5and8; all other proposals unchanged.',
        'mechanism': 'Each original ordered pair has equal mass1/(n*(n-1)). Conditional on unequal '
                     'resource labels, sample one uniform integer in0..M-1 where M=n*n-sum(count_r^2); '
                     'map bijectively to first-position block of lengthn-count(label), then a second '
                     'position with a different label. One actual candidate; no resampling loop, '
                     'objective preview or generated-candidate rejection. No new parameter.',
        'engineering': 'Actual frozen Intra class/source resolution and SHA/JDK; OFF shadow100k '
                       'for both methods/instances seed12390003 equals existing baseline full paidSHA, '
                       'fronts/genes/birthFE, initials, ledger, search and decoder counts. Exhaustive '
                       'ternary vectors length0..6 prove uniform ordered-pair support exactly. ON '
                       'cutoffs1/2/5100/10000 on bothinstances preserve actualFE accounting and fullQA. '
                       'All engineering before32performance runs; no observer trace used for timing.',
        'budgets': '32runs:16fixed100kFE=1600000successFE;16trueTIME_LIMIT4/5s=72s search, each500kFE '
                  'safety cap. HittingFEcap beforeT is incomplete, not a time result. Engineering '
                  '4*100kOFF+2*(1+2+5100+10000)ON=430206successFE. Totalnew fixed2030206FE plus '
                  'actual time-run attempts, at most10030206attemptFE if alltimecaps reached. '
                  'One JVM sequential Xms32m/Xmx2g. Input/model100initials equal perinstance/seed '
                  'and all4arms/budgets; originalnatural VNS depth and all roles/Q/family/sharing unchanged.',
        'metrics': 'PrimaryHV1.5 at declared100kFE and trueT. Sensitivity1.25/2 unchanged scales. '
                  'IGD+ common empiricalND union of4arms*2seeds at eachinstance/budget; no search use. '
                  'Report individual seeds, missing FE checkpoints, interruptions, stage fees and all '
                  'registered curves; do not choose early windows. No mixingFE/time frontiers.',
        'gate': 'Bothinstances, eachbudget: FULL_ON medianHVvsFULL_OFF>=0%, everypair>=-0.5%; '
                'TIME medianvsFULL_OFF>=0.5%. Bothbudgets medianvsNSGA_ON>=-1%, everypair>=-5%. '
                'Ref1.25/2 medians>=0vsFULL_OFF and>=-2%vsNSGA_ON. IGD+symmetrical worsening '
                'median<=5%vsNSGA_ON. All necessary to justify full500k and duty/share/Li/common '
                'original sharing comparisons later. Failure stops this exact conditional kernel '
                'without changingpair rule, gate, seed, T, local depth or target operators.',
        'scope': 'Common operator engineering/search-distribution modification, not a new main '
                 'four-duty innovation, full algorithm confirmation, fatigue specificity or guaranteed '
                 'publication. A pass only permits further complete comparison. Default mainline, '
                 'previous stopped experiments and model protected. No downloads/transfers/push.'}
