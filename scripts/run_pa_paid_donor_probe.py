"""One fixed costed source/recipient mechanism study, preserving original jointly copied job packets."""
import os
os.environ["OMP_NUM_THREADS"]="1"
os.environ["OPENBLAS_NUM_THREADS"]="1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from pa_capability_support import SOURCE,run_case,initial_key,fees
from pa_paid_donor_build import build,INTERFACE
from pa_paid_donor_data import initial_records,write_initial,write_pool,at
from pa_paid_donor_replay import audit
from pa_paid_donor_analysis import analyze,readiness
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest

ENGINE=ROOT/"runs/pa-population-engineering-20261105-164116-698339"
SOURCES={"S":("FULL_SHARED_DEEP",False),"U":("FULL_SHARED_DEEP",True),"N":("NSGA2_DEEP",False)}


def protocol():
    old=read(ROOT/"runs/pa-base-qualification-20261105-180835-751659/protocol.json")
    return {"version":"PA_PAST_PAID_JOINT_SUPPLY-v1","registered":"2026-11-06","seeds":[14330003,14330037],
        "instances":[{"stem":s["stem"],"normalization":s["normalization"]} for s in old["instances"]],
        "sourceAlgorithms":SOURCES,"prefixFE":50000,"receiverFE":50000,"logicalTotalFE":100000,
        "sourceRuns":"Each source paid100k, own continuation is the100kendpoint. Only exact50ksnapshot used for imports; future50knever enters recipient",
        "memory":"100uniform-with-replacement sampled pastpaid states, same fixed capacity and independent sampler for initial/NDpools; no objective ranking",
        "recipientSeed":"sourceSeed XOR0x73164c9d, shared acrossrecipientarms; four roles15/55/15/15, unchanged atomic job-packet mixing",
        "recipientModes":["PURE100koriginalinitials","INIT_GRAFT50kinitialpaiddonors","GRAFT_S/U/N50kpastNDdonors","INHERIT_S/U/N50ksameNDsampleasinitials,noborrow"],
        "endpoints":"Per source: NDunion(source50k,recipient50k). NONEusesPURE'spaid50kprefix. INITusescommonINIT_GRAFT. SELFsource100kandPURE100k included.16logical endpoints percontext",
        "realCost":"3source100k +PURE100k +7recipient50k=750k/context;4contexts=3000000newactualscienceFE. Source prefixes and sharedreceiverbranches reused, not64independent experiments",
        "sameInitials":"Allsources begin with same100fresh fourvectors/objectives. Allnoninheritrecipients re-evaluate them as part of50k; INHERIT deliberately re-evaluates sampledknown states. No free initialization",
        "sourceUniform":"ExistingSHARE_JOB_ALIGNED_UNIFORMpreference; QGStables/guidance remain active, no uniform-random-guide substitution; learnedvalues/paths maydiffer",
        "donation":"Uniform among99otherliveworkingstates+100fixedmemoryviews, no memory ratio/score learning. CompleteFMW+key jobpackets only. Importedpoints never free-enter working population/archive",
        "teacherViews":"Physical-neutral per-generation reencoding by independent seed/gen/slot RNG; no working RNG advances. NONEmaintains same memoryview machinery for parity",
        "sourceLimits":"A50kprefix maynot finish all physicalgroups' deepLS. Record actual sourcecoverage; no claim everyprofessional localrole contributed. Imported role tags are neutral, not producer credit",
        "engineeringFE":137200,"scientificFE":3000000,"maximumQuestionFE":3137200,
        "engineering":"Bothinstances: old/new SPECIAL5200paid parity,UNIFORM5200andNSGA5200; NONEandGRAFTtwofullrecipientgenerations withallpaidfulltimelineQA/importQA/independentviews/mixing reconstruction",
        "metrics":"Commonfrozennormalization;HV1.5with1.25/2;IGD+NDunionofall16logicalmethods x2seedsperinstance; rawweakbidirectionalCincludingequality",
        "primary":"GRAFT_S, notposthoc bestsource/mode",
        "necessaryComparisons":"BOTHinstances vsNONE_S/INIT_S/INHERIT_S/SELF_S/PURE/GRAFT_U:medianHV>=0.5%,IGD+worsening<=0,Cdelta>=0; perseedHV>=-1%,IGD+<=5%,Cdelta>=-0.02; sensitivitymedianHV>=0",
        "strongOrdinary":"vsGRAFT_NandSELF_N:medianHV>=-1%,IGD+<=5%,Cdelta>=-0.02; perseedHV>=-5%,IGD+<=15%,Cdelta>=-0.1;sensitivitymedianHV>=-1%",
        "interpretation":"Project resource margins, not statisticalsignificance, universal constants or contribution veto; all3joint, no weighted score/vote",
        "sampling":"Completeall44scientific JVMruns beforeaggregateanalysis; no seed changes, intermediate-win stopping,50/50split/poolsize tuning orchoosingN/Uasnewprimary",
        "time":"No sameTIMEclaim: sourceprefixclock and recipientclock/loader/QA recorded; staged JVM prototype is not a commonwall-deadline implementation",
        "scope":"Newmechanism only; no revival of stoppedTYPED,oldlearnedtreeorordinaryqualification. MainlineQGS/families/sharing untouched",
        "defaultMainlineChanged":False,"goalAchieved":False}


def native_receiver(root,cp,stem,mode,teacher,completed):
    folder=root/stem/("ENGINEERING-"+mode);out=folder/"audit";out.mkdir(parents=True)
    limit=7900 if stem=="20_8_5_1" else 39900;inp=root/stem/"inputs"
    files=[inp/(stem+".txt"),inp/"RECONSTRUCTED-setup.txt",inp/"fatigue-input.txt",SOURCE/stem/"11730007/sources.tsv"]
    cmd=["java","-Xms32m","-Xmx2g","-Dresearch.snapshot.mode=ANCHOR","-Dresearch.pa.traceIdentity=true",
        "-Dresearch.pa.borrowMode="+mode,"-Dresearch.pa.borrowTSV="+str(teacher),"-Dresearch.pa.borrowSeed=13630003",
        "-Dresearch.pa.borrowQA=true","-Dresearch.pa.borrowTrace="+str(out/"borrowed-views.jsonl"),"-cp",cp,
        "research.dynamic.PaPopulationRun",*map(str,files),str(out),"13630003",str(limit)]
    write_once(folder/"command.json",cmd);write_once(folder/"input-hashes.json",{str(p):digest(p) for p in [*files,teacher]})
    execute(cmd,folder/"run.log",timeout=600)
    result=audit(out,mode);receipt,=rows(out/"receipt.jsonl")
    if mode=="NONE":assert result["paidSHA256"]==read(ENGINE/stem/"main/audit/independent-replay.json")["paidSHA256"]
    else:assert result["externalReads"]>0
    assert receipt["completedGenerations"]==2 and receipt["borrow"]["borrow.fullQA"]==300
    return {"stem":stem,"mode":mode,"result":result,"receipt":receipt}


def engineering(root,cp,completed):
    results=[];source_proof=ROOT/"runs/pa-typed-basis-pilot-20261105-231059-489346"
    for stem in ("20_8_5_1","100_2_3_1"):
        original_cp=(INTERFACE/"classpath.txt").read_text("utf-8-sig").strip();expected=None;initial=None
        for label,arm,uniform,usecp in (("REF_S","FULL_SHARED_DEEP",False,original_cp),("NEW_S","FULL_SHARED_DEEP",False,cp),
                                      ("NEW_U","FULL_SHARED_DEEP",True,cp),("NEW_N","NSGA2_DEEP",False,cp)):
            out,receipt=run_case(root,usecp,stem,arm,"ENGINE-"+label,5200,13630003,audit=True,vm_settings={"research.pa.sourceUniform":str(uniform).lower()})
            completed.append((out,receipt));key=initial_key(out)
            if initial is None:initial=key
            else:assert key==initial
            if label=="REF_S":expected=receipt["paidSHA256"]
            if label=="NEW_S":assert expected==receipt["paidSHA256"]
            if label in ("NEW_S","NEW_U"):
                names=("MAKESPAN","CENTER","ENERGY","WORKER_COST") if not uniform else ("CENTER",)*4
                for g,name in enumerate(names,1):
                    n=receipt["search"][f"qgs.g{g}.updates"];assert n>0 and receipt["search"][f"qgs.g{g}.preference.{name}"]==n
                    assert sum(receipt["search"].get(f"qgs.g{g}.action{a}",0) for a in range(3))==n
        old=source_proof/stem/"14230003/FE100K-FULL_SHARED_DEEP"
        _,points=at(old,50000)
        teacher=root/stem/"engineering-teachers.tsv";write_pool(teacher,points,13630003,old,"ENGINEERING_PAST_PREFIX")
        for mode in ("NONE","GRAFT"):results.append(native_receiver(root,cp,stem,mode,teacher,completed))
    write_once(root/"engineering.json",{"passed":True,"receivers":results,"sourceParityAndUniformQTablesActive":True})
    print("PA_PAID_DONOR_ENGINEERING_PASSED",flush=True)


def science(root,cp,plan,completed):
    for i,spec in enumerate(plan["instances"]):
        stem=spec["stem"]
        for j,seed in enumerate(plan["seeds"]):
            folder=root/stem/str(seed);folder.mkdir(parents=True);expected=None
            order=list(SOURCES);shift=(i+j)%3
            for name in order[shift:]+order[:shift]:
                arm,uniform=SOURCES[name]
                out,receipt=run_case(root,cp,stem,arm,f"{seed}/SOURCE_{name}",100000,seed,
                    vm_settings={"research.pa.sourceUniform":str(uniform).lower()})
                completed.append((out,receipt));key=initial_key(out)
                if expected is None:expected=key
                else:assert key==expected
            first=initial_records(folder/"SOURCE_S");raw_initial=folder/"raw-initial.tsv";write_initial(raw_initial,first)
            init_memory=folder/"initial-teachers.tsv";write_pool(init_memory,first,seed,folder/"SOURCE_S","INITIAL_RANDOM")
            teacher_files={}
            for name in SOURCES:
                _,points=at(folder/("SOURCE_"+name),50000)
                teacher=folder/("teachers-"+name+".tsv");write_pool(teacher,points,seed,folder/("SOURCE_"+name),"SOURCE_ND_AT_50000")
                teacher_files[name]=teacher
            target_seed=seed ^ 0x73164c9d
            cases=[("PURE",100000,"NONE",raw_initial,init_memory),("INIT_GRAFT",50000,"GRAFT",raw_initial,init_memory)]
            for name,teacher in teacher_files.items():
                cases += [("GRAFT_"+name,50000,"GRAFT",raw_initial,teacher),("INHERIT_"+name,50000,"NONE",teacher,teacher)]
            shift=(i+j)%len(cases)
            for label,limit,mode,initial,teacher in cases[shift:]+cases[:shift]:
                out,receipt=run_case(root,cp,stem,"PA_JOINT",f"{seed}/{label}",limit,target_seed,source_tsv=initial,
                    vm_settings={"research.pa.borrowMode":mode,"research.pa.borrowTSV":str(teacher),"research.pa.borrowSeed":str(target_seed)})
                completed.append((out,receipt));assert receipt["search"]["borrow.memory"]==100
                if mode=="GRAFT":assert receipt["search"]["borrow.externalReads"]>0
                else:assert receipt["search"]["borrow.externalReads"]==0
                if not label.startswith("INHERIT"):assert initial_key(out)==expected
            print("PA_PAID_DONOR_CONTEXT_COMPLETE",stem,seed,flush=True)


def total(root,completed):
    result=fees(completed);native=[r for p in root.glob("*/ENGINEERING-*/audit/receipt.jsonl") for r in rows(p)]
    result["nativeEngineeringFE"]=sum(r["successfulFE"] for r in native)
    result["totalActualFE"]=result["successfulFE"]+result["nativeEngineeringFE"]
    result["nativeEngineeringFullQA"]=sum(r["fullDecoderQA"] for r in native)
    result["importedTeacherFullQA"]=sum(r["borrow"]["borrow.fullQA"] for r in native)
    result["totalFullQA"]=result["offlineFullDecoderQA"]+result["nativeEngineeringFullQA"]+result["importedTeacherFullQA"]
    result["totalFailedEvaluations"]=result["failedAttempts"]+sum(r["failedFE"] for r in native)
    return result


def main():
    with controller_lock(ROOT/"research/night_research","dispatch.lock"):
        root=ROOT/"runs"/datetime.now().strftime("pa-paid-donor-probe-%Y%m%d-%H%M%S-%f");root.mkdir();plan=protocol()
        write_once(root/"protocol.json",plan);print("PA_PAID_DONOR_ROOT",root,flush=True);completed=[]
        try:
            for spec in plan["instances"]:shutil.copytree(SOURCE/spec["stem"]/"inputs",root/spec["stem"]/"inputs")
            cp=build(root)
            for name in ("run_pa_paid_donor_probe.py","pa_paid_donor_build.py","pa_paid_donor_data.py","pa_paid_donor_replay.py","pa_paid_donor_analysis.py","pa_capability_support.py"):
                shutil.copy2(Path(__file__).with_name(name),root/"source"/name)
            write_once(root/"controller-hashes.json",{p.name:digest(p) for p in (root/"source").glob("*.py")})
            engineering(root,cp,completed);science(root,cp,plan,completed)
            result=analyze(root,plan);gate=readiness(result);counts=total(root,completed)
            assert counts["totalActualFE"]==3137200 and counts["totalFailedEvaluations"]==0
            decision="PAID_JOINT_SUPPLY_PROMISING_ONLY" if gate["pass"] else "STOP_FIXED_PAID_JOINT_SUPPLY"
            write_once(root/"analysis.json",{**result,"readiness":gate,"decision":decision,**counts,"goalAchieved":False})
        except BaseException as error:
            write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","error":repr(error),"completedCommonRuns":len(completed),**total(root,completed)})
            raise
        write_once(root/"status.json",{"status":"COMPLETE","decision":decision,**total(root,completed),"goalAchieved":False})
        print("PA_PAID_DONOR_COMPLETE",decision,total(root,completed),flush=True)


if __name__=="__main__":main()
