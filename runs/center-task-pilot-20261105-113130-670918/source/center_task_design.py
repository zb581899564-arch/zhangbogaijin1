"""Generation-owned CENTER task lifecycle pilot; all budgets and controls frozen before outcomes."""
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, write_once

SOURCE = ROOT / 'runs/natural-regime-bench-20261105-073626-086353'
CAPACITY = ROOT / 'runs/center-task-capacity-20261105-104759-691496'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (13050003, 13050033)
ARMS = ('OFF', 'OWNER_PDDR', 'EQUAL', 'PERMUTE', 'FIXED', 'NSGA')
LIMIT = 13301
PRIMARY = 13300
CUTOFFS = (1, 2, 2000, 5341, 5348, 13300)


def design():
    return {
        'source': str(SOURCE), 'capacityPrerequisite': str(CAPACITY),
        'instances': read(SOURCE / 'protocol.json')['instances'], 'freshSeeds': SEEDS, 'arms': ARMS,
        'hypothesis': 'Generation-owned compromise targets can create useful progress through '
                      'personal choice, global comparison, local search and global/local retention, '
                      'beyond mere slot ownership, one common scalar target or nonpersistent targets.',
        'lifetime': 'Native100population is regrouped each generation. Every role gets metadata; '
                    'CENTER55slots get tasks for that generation only. FixedFA/family grouping unchanged. '
                    'Task ids survive each own parent/child and global/local pair; next native regroup '
                    'rebuilds owners. Do not call them permanent particle roles across generations.',
        'scalarization': 'Same55positive integer-sum12weights, fixed source scale, ideal=min over '
                         'only successfully paid objective observations. Both sides of a comparison '
                         'use the same current ideal; no cached scalar values or future ideals. '
                         'Task metadata never changes the physical decoder/cache key.',
        'policies': {
            'OFF': 'Unchanged original FULL_ROLE search, PDDR local and original200to100survival.',
            'OWNER_PDDR': 'Same new owner lifecycle/pair retention as task variants, native personal '
                          'guide/Q reward/local PDDR, CENTERglobal pair PDDR on full110pool; final '
                          'CENTERpair PDDR on full200pool. NonCENTERend pairs use own raw objective.',
            'EQUAL': 'Owned lifecycle with all CENTERtargets(1/3,1/3,1/3).',
            'PERMUTE': 'Same55direction marginals, reassign across slots at each CENTERglobal batch '
                       'and before local phase. Assignment uses separate registered RNG, not search RNG.',
            'FIXED': 'Slot i keeps direction i throughout one whole global/local/retention generation.',
            'NSGA': 'Existing standardNSGA-II with matched original deep-local kernel/physical quotas; tasks OFF.'},
        'coherentChanges': 'Scalar modes choose personal guide by the current task from own ND history; '
                           'CENTERglobal retains own parent/child by strict task improvement; CENTERlocal '
                           'accepts strict task improvement; existing Q table uses mean relative task '
                           'progress for CENTERreward. No new Qtable/action, guide source or operator. '
                           'Other-role global rules, objectives and Q rewards remain original.',
        'survival': 'All enabled variants use100own global/local pairs at generation end, preserving '
                    'full80/5/5/5/5family totals and all55CENTERtask slots. This changes boundary end '
                    'retention too, hence OWNER_PDDR/EQUAL/PERMUTE matched lifecycle controls are mandatory. '
                    'Original full-poolPDDR scores still recorded as diagnostics, not mislabeled as task decisions.',
        'budget': 'Each run100initial+2*(5000global+1600local)+1next-global=13301actual successFE. '
                  'Each generation100visits, pervisit2inter+14intra at one registered factory. '
                  'Primary quality checkpoint13300, final extra1FE only lets second retention complete '
                  'and checks next generation; final13301secondary, never pick the better endpoint. '
                  '24pilot runs=319224FE; OFF original/shadow engineering4runs=53204FE; '
                  'six FIXED cutoff checks sum25992FE. Total planned398420successfulFE.',
        'ledger': 'Two generations of native physical groups15/55/15/15, every visit2inter+14intra. '
                  'Factories drawn once from independent seed xor0x71a9; identical per instance/seed '
                  'across arms. No new restart rule: original fixed-ledger fill/restarts retained. '
                  'This is a bounded complete-lifecycle mechanism pilot, not evidence about deep500k '
                  'or natural local stopping. A pass must later survive those original full regimes.',
        'engineering': 'Resolve/copy actual frozen class sources/hashes/JDK. OFF vs original two-instance '
                       'seed12390003same13301FE ledger: full paid SHA, common FE fronts/genomes, initial '
                       'vectors/objectives, exact local ledger/search and decoder-operation counts. '
                       'Zero-decoder known scalar/pbest/slot identity fixtures. FIXEDcutoffs1/2/2000 '
                       '/5341/5348/13300verify paid budgets, last acquired decode, partial ledger, '
                       'local finally cleanup. Any failure stops before24science runs.',
        'entryAmendment': 'Isolated entry permits replay-prefix cleanup when FE remaining==0 as well '
                          'as true time deadline, instead of falsely demanding unspent future slots. '
                          'No ordinary full13301ledger effect. Original entry unchanged. Source checkpoints '
                          'extended to1/2/100/5100/6700/11700/13300/13301, all actual paid states only.',
        'gate': 'Both instances, pair fresh seeds: primary13300medianFIXED HV gain>=1%overOFF, '
                'each seed nonnegative; median>=0.5%overeachOWNER_PDDR/EQUAL/PERMUTE; median>=0%vsNSGA; '
                'refs1.25/2median directions vsOFF/NSGA nonnegative. IGD+ symmetric worsening median '
                'vsNSGA<=5%, no individualHV tail worse than-10%vsNSGA. Median measuredFE-run '
                'search-cost ratio<=1.25 vsOFF/NSGA. All necessary. Failure stops this fixed '
                'generation-owned55-direction architecture without weight/ideal/ownership/ledger/seed scans.',
        'metrics': 'PrimaryHVref1.5 fixed scales. Per-instance empiricalIGD+ reference ND union of '
                   'all12primaryfronts at that instance (all arms/seeds), never used in search. '
                   'Report13,301secondary and registered stage curves separately; no early endpoint promotion.',
        'nextIfPass': 'Only native/time-cost and full deep/natural regime protocol, with standard '
                      'MOEA/D orMPSO/D+matchedlocal control (not currently wired in the deepNSGA-only '
                      'wrapper), original shared/Li, duty/share ablations, trueTIME and fresh-instance '
                      'screen. Pilot lacks this complete comparison and cannot establish contribution/goal completion.',
        'limits': 'Generic decomposition is established. This is not a novel scalarization, complete '
                  'same-time result, fatigue specificity, independent confirmation or faithful Li author '
                  'result reproduction. Production/default, physical model, role counts, Q parameters, '
                  'global kernel/families/shared pool/selector unchanged. No downloads or transfers.'
    }


def prepare_inputs(root):
    for stem in STEMS: shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')


def ledger(path, stem, seed):
    generator = np.random.default_rng(seed ^ 0x71A9)
    lines = ['visit,group,round,factory,paid,restarts']; visit = 0
    for generation in range(2):
        for group, count in ((1, 15), (2, 55), (3, 15), (4, 15)):
            for _ in range(count):
                visit += 1; factory = int(generator.integers(int(stem.split('_')[2])))
                lines.append(f'{visit},{group},-1,-1,2,0')
                lines.append(f'{visit},{group},0,{factory},14,0')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def run_order():
    order = []
    for i, stem in enumerate(STEMS):
        for j, seed in enumerate(SEEDS):
            offset = (i + j) % len(ARMS)
            order += [{'stem': stem, 'seed': seed, 'arm': arm} for arm in ARMS[offset:] + ARMS[:offset]]
    return order
