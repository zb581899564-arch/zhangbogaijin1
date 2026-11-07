"""Frozen zero-FE audit of role-conditional structure versus ordinary-region and sample controls."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from research.semantic_repair.evidence import digest
from pa_role_context_data import snapshots, identifiability, pair_data, group_folds
from pa_role_context_scores import cross_validate, math_checks

SOURCE = ROOT / "runs/pa-paid-donor-probe-20261106-001143-747475"


def protocol():
    return {"version": "PA_ROLE_CONTEXT_STRUCTURE_ZERO_FE-v1", "registered": "2026-11-06",
            "source": str(SOURCE), "newSearchFE": 0, "newDecoderCalls": 0,
            "datasets": "6 unique native engineering model inputs plus4 paid scientific initial populations; identical NONE/GRAFT first model counted once",
            "features": "Actual factory-pair categorical distributions and within-factory physical order; noM/W marginal substituted for actualmodel features",
            "queries": "All100workingpoints; exact physical genotype duplicate weights sumto1; grouping uses genes only, not objectives",
            "folds": "5 deterministic SHA256 folds, separately blocked by physicalgenotype and wholeFApattern. Same groups never cross train/test",
            "models": ["GLOBALalltraining", "ROLEsamepreference", "RANDOM_MATCHED16uniformsame-ntraining draws",
                       "OBJECTIVE_NEAREST_MATCHEDsame-ntraining neighbors in existing frozen normalizedobjectives"],
            "scores": "HeldoutfactorypairNLLlower, joint-vs-independentloggainhigher, samefactoryorderNLLlower; commonJeffreys0.5cellprior. No feature/alpha/fold tuning",
            "regionControl": "Simple objective nearestneighbors with equal training count, not an implementation of fullMO-GOMEA clustering",
            "fallback": "EmptyroletrainingusesGLOBALforROLEandbothsame-sizecontrols; recorded, no droppedqueries",
            "interpretation": "Structural likelihood is diagnostic, not decoder objective performance, acceptance quality, innovation or scientific confirmation",
            "decision": "Do not launch role-specific model on distribution difference alone. Descriptive role signal is consistent onlyifROLE beatsGLOBALandOBJECTIVE_NEARESTon factoryNLLand dependencegain, and is not worse on orderNLL, at bothfoldtypes in all4 generation2engineeringinputs. Otherwise stopthis explanationas immediatepaidmechanismbasis",
            "notGlobalVeto": "Failure stops this engineering-input argument, not fourroles or allconditionalmethods. Even successneedsproperactual-search observation and ordinaryregioncontrol beforepaidperformance",
            "costQualification": "No search, decoder, newselector, operator or change to frozen decisions; time and bootstrap costs not performance evidence"}


def descriptive_decision(results):
    checked = []
    for item in results:
        if item["kind"] != "ENGINEERING" or item["generation"] != 2:
            continue
        folds = {}
        for kind, result in item["crossValidation"].items():
            role = result["overall"]["ROLE"]
            controls = (result["overall"]["GLOBAL"], result["overall"]["OBJECTIVE_NEAREST_MATCHED"])
            folds[kind] = bool(not result["fallbacks"] and all(
                role["factoryPairNLL"] < control["factoryPairNLL"] - 1e-12
                and role["jointVsIndependentGainNats"] > control["jointVsIndependentGainNats"] + 1e-12
                and role["sameFactoryOrderNLL"] <= control["sameFactoryOrderNLL"] + 1e-12 for control in controls))
        checked.append({"id": item["id"], "foldConditions": folds, "pass": all(folds.values())})
    assert len(checked) == 4
    return {"checks": checked, "consistentDescriptiveRoleSignal": all(row["pass"] for row in checked),
            "goalAchieved": False, "scientificPerformanceProved": False}


def report(root, results, decision):
    lines = ["# 职责条件结构：零FE阻断检验", "", "这是结构预测诊断，不是算法性能或创新判定。GEN1输入两分支重复已去重；各代/分支仍非独立实验。", "",
             "NLL越小越好，JointGain为相对同一模型边际独立假设的对数增益、越大越好；值为nats/pair。相同工厂顺序NLL仅在查询同厂工件对上计。", "",
             "PHYSICAL阻断相同排程；FACTORY阻断相同完整FA。训练相同数量的普通目标近邻与随机子集对照保留。", "",
             "|输入|阻断|方法|工厂对NLL|JointGain|同厂顺序NLL|空职责回退查询|", "|---|---|---|---:|---:|---:|---:|"]
    for item in results:
        for kind, result in item["crossValidation"].items():
            fallback = sum(row["queries"] for row in result["fallbacks"])
            for method, score in result["overall"].items():
                order = score["sameFactoryOrderNLL"]
                lines.append(f'|{item["id"]}|{kind}|{method}|{score["factoryPairNLL"]:.6f}|{score["jointVsIndependentGainNats"]:.6f}|{order:.6f}|{fallback}|')
    lines += ["", "## 停止范围", "", str(decision), "",
              "全部逐职责/训练回退/可辨识性数据见analysis.json。原科学三指标停止与默认主线未改，本次搜索FE和解码均0。", ""]
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-role-context-audit-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        write_once(root / "protocol.json", protocol())
        source = root / "source"
        source.mkdir()
        for name in (Path(__file__).name, "pa_role_context_data.py", "pa_role_context_scores.py"):
            shutil.copy2(Path(__file__).with_name(name), source / name)
        write_once(root / "source-hashes.json", {p.name: digest(p) for p in source.iterdir()})
        print("PA_ROLE_CONTEXT_ROOT", root, flush=True)
        try:
            write_once(root / "math-checks.json", math_checks())
            plan = read(SOURCE / "protocol.json")
            specs = {p["stem"]: p for p in plan["instances"]}
            data = snapshots(SOURCE, plan)
            write_once(root / "working-snapshots.json", data)
            results = []
            for i, snapshot in enumerate(data):
                spec = specs[snapshot["stem"]]
                factories = int(snapshot["stem"].split("_")[2])
                pairs = pair_data(snapshot["points"], factories, spec["normalization"])
                checked = {}
                for j, kind in enumerate(("PHYSICAL", "FACTORY")):
                    folds, weights = group_folds(snapshot["points"], kind)
                    checked[kind] = cross_validate(pairs, folds, weights, 0x618fac + i * 19 + j)
                results.append({**{k: v for k, v in snapshot.items() if k != "points"},
                                "identifiability": identifiability(snapshot["points"]), "crossValidation": checked})
                print("PA_ROLE_CONTEXT_INPUT_COMPLETE", snapshot["id"], flush=True)
            decision = descriptive_decision(results)
            write_once(root / "analysis.json", {"datasets": results, "decision": decision,
                                               "newSearchFE": 0, "newDecoderCalls": 0})
            report(root, results, decision)
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), "newSearchFE": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "decision": decision, "newSearchFE": 0, "newDecoderCalls": 0})
        print("PA_ROLE_CONTEXT_COMPLETE", decision, flush=True)


if __name__ == "__main__":
    main()
