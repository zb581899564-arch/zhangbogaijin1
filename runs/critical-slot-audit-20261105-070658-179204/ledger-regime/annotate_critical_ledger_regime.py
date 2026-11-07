"""Zero-FE provenance and restart description of the observed fixed local-budget regime."""
import csv
from pathlib import Path
import shutil
import sys
from run_long_budget_bridge import ROOT, read, rows, write_once
from paired_survival_bench import ANCHOR


def ledger(path):
    with path.open(encoding='utf-8') as stream:return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]


def main():
    root=Path(sys.argv[1]).resolve();out=root/'ledger-regime';out.mkdir();shutil.copy2(__file__,out/Path(__file__).name)
    template=ANCHOR/'SPECIAL-LINEAR/local-ledger.csv';base=ledger(template)
    command=read(ANCHOR/'SPECIAL-LINEAR/command.json');entry=command.index('research.dynamic.PddrIsolationRun')
    keys=('visit','group','round','paid');quota=lambda data:[tuple(r[k] for k in keys) for r in data]
    cases=[]
    for case in read(root/'analysis.json')['cases']:
        folder=root/case['stem']/case['method'];actual=ledger(folder/'ledger-input.csv');assert quota(actual)==quota(base)
        observed=rows(folder/'critical-slots.jsonl');dead=[r for r in observed if r['strictMakespanImprovementImpossible']]
        cases.append({'stem':case['stem'],'method':case['method'],'sameVisitGroupRoundAndPaidAsOldTemplate':True,
            'MrestartCount':sum(r['restarts'] for r in observed),'impossibleMrestartCount':sum(r['restarts'] for r in dead),
            'impossibleMslotsWithRestart':sum(r['restarts']>0 for r in dead),'impossibleMslots':len(dead),
            'actualFactoryDiffersFromNativeDrawMslots':sum(r['factory']!=r['drawnFactory'] for r in observed)})
    result={'templateLedger':str(template),'templateInput':command[entry+1],'templateQuotaSlots':len(base),'quotaKeysCompared':keys,
        'factoryRegenerationImplementation':str(ROOT/'scripts/paired_survival_bench.py'),
        'factoryRule':'prepare(): regenerate every intra-slotfactory by independent numpy RNG(seed xor0x5A17), with current instanceF. '
                      'The quota/visit schedule is inherited from20_2_3_1, not each current trajectory natural stopping.',
        'cases':cases,'newSearchFE':0,'additionalDecodes':0,
        'limits':'Protocol provenance, not proof of unfair ranking or proof a natural variant will win. All methods had matching local quotas. '
                 'Previous findings remain conditional on their declared replay regime; complete natural-stopping behavior requires separate evidence.'}
    write_once(out/'annotation.json',result);print('LEDGER_REGIME',result)


if __name__=='__main__':main()
