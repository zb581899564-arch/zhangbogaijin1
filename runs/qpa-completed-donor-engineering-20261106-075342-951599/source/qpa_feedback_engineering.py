"""Minimal frozen-source override and independent donor-source reconstruction."""
from pathlib import Path
import hashlib
import json
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from qpa_engineering_replay import Replay
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes


def build(root,source):
    target=root/'source';classes=root/'classes';target.mkdir();classes.mkdir()
    raw=(source/'source/QpaPopulation.java').read_text('utf-8-sig')
    old='QpaIndividual donor = parents.get(donorSlot);';assert raw.count(old)==1
    raw=raw.replace(old,'QpaIndividual donor = QpaCompletedDonors.choose(parents, offspring, donorSlot, working.role);')
    (target/'QpaPopulation.java').write_text(raw,encoding='utf-8')
    for p in (ROOT/'src/algorithms/diagnostics/qpa_feedback').glob('*.java'):shutil.copy2(p,target)
    for name in ('run_qpa_completed_donor_engineering.py','qpa_feedback_engineering.py'):
        shutil.copy2(Path(__file__).with_name(name),target)
    base=(source/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*[str(p) for p in target.glob('*.java')]],root/'compile.log')
    cp=str(classes)+';'+base;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in target.iterdir()});write_once(root/'class-hashes.json',class_hashes(classes))
    write_once(root/'original-population-source.json',dict(path=str(source/'source/QpaPopulation.java'),sha256=digest(source/'source/QpaPopulation.java')))
    return cp


class FeedbackReplay(Replay):
    def __init__(self,catalog,receipt,mode,cuts):
        super().__init__(catalog,receipt);self.mode=mode;self.wanted.update(cuts);self.fresh=0;self.cross=0;self.reads=0

    def step(self,event):
        slot=event['donorSlot'];old=self.parents[slot];donor=old;receiver=self.states[self.working]
        if slot<len(self.offspring):
            available=self.offspring[slot]
            if self.mode=='ALL' or self.mode=='OWN' and self.states[available]['role']==receiver['role']:donor=available
        assert self.states[donor]['paidFE']<event['paidFE']
        if event['phase']==1:
            self.reads+=1;self.fresh+=donor!=old;self.cross+=donor!=old and self.states[donor]['role']!=receiver['role']
        self.parents[slot]=donor
        try:super().step(event)
        finally:self.parents[slot]=old


def replay(folder,mode,cuts):
    catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl');check=FeedbackReplay(catalog,receipt,mode,cuts)
    handlers={'initial':check.initial,'model':check.model,'step':check.step,'programEnd':check.program_end,'generationEnd':check.generation_end}
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line);handlers[event['kind']](event)
    result=check.finish();helper,=rows(folder/'completed-donor-identity.jsonl');counts=helper['reads']
    assert counts['mode']==mode and counts['maskReads']==check.reads and counts['freshMaskReads']==check.fresh and counts['crossRoleFreshMaskReads']==check.cross
    result.update(freshMaskReads=check.fresh,crossRoleFreshMaskReads=check.cross);return result


def trajectory(folder):
    raw=[];schedule=hashlib.sha256();first=None;model=None;parent_ids=None
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            e=json.loads(line)
            if e['kind'] in ('initial','step'):raw.append(e['rawPaidHash'])
            if e['kind']=='model' and e['generation']==1:model=e['activeSubsets'];parent_ids=[p['id'] for p in e['parents']]
            if e['kind']=='step' and e['generation']==1:
                schedule.update((json.dumps([e[k] for k in ('generation','slot','step','subset','phase','donorSlot','reference')])+ '\n').encode())
                if e['donorId']!=parent_ids[e['donorSlot']] and first is None:first=e['paidFE']
    return dict(raw=raw,drawSHA256=schedule.hexdigest(),activeSubsets=model,firstFreshFE=first)


def run_one(root,cp,spec,mode,label,limit,generations):
    out=root/spec['stem']/label;out.mkdir(parents=True);inputs=root/spec['stem']/'inputs'
    command=['java','-Xms32m','-Xmx2g','-Dresearch.snapshot.mode=ANCHOR','-Dresearch.pa.traceIdentity=true',
        '-Dresearch.qpa.completedDonors='+mode,'-cp',cp,'research.dynamic.QpaFeedbackRun',
        *[str(inputs/name) for name in (spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt')],str(out),'14670003',str(limit),str(generations)]
    write_once(out/'command.json',command);print('QPA_FEEDBACK_RUN',spec['stem'],label,limit,flush=True)
    execute(command,out/'run.log',timeout=600)
    capture,=rows(out/'loaded-identity.jsonl');write_once(out/'identity-verified.json',verify_capture(capture,cp))
    helper,=rows(out/'completed-donor-identity.jsonl');write_once(out/'completed-donor-identity-verified.json',verify_capture(helper['identity'],cp))
    return out
